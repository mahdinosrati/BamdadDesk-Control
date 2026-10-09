import json
import re
import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from .scopes import device_in_scope, group_allowed


class ConnectionEvent(BaseModel):
    model_config = ConfigDict(extra='forbid')
    event_id: str = Field(pattern=r'^[a-zA-Z0-9-]{16,64}$')
    session_id: str = Field(pattern=r'^[a-zA-Z0-9-]{1,100}$')
    kind: Literal['opened', 'authorized', 'closed']
    occurred: int = Field(ge=1)
    peer_id: str = Field(default='', max_length=100)
    peer_name: str = Field(default='', max_length=100)
    peer_ip: str = Field(default='', max_length=64)
    connection_type: int = Field(default=0, ge=0, le=4)


class EventBatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    events: list[ConnectionEvent] = Field(min_length=1, max_length=32)


def scoped_events(db, admin, device_id='', days=30, before=9223372036854775807, limit=200):
    clauses = ['e.occurred>=?', 'e.id<?']
    values = [int(time.time()) - days * 86400, before]
    if device_id:
        device_in_scope(db, admin, device_id)
        clauses.append('e.device=?')
        values.append(device_id)
    if admin['groups'] is not None:
        marks = ','.join('?' for _ in admin['groups']) or 'NULL'
        clauses.extend([f'e.group_id IN ({marks})', f'd.group_id IN ({marks})'])
        values.extend(admin['groups'])
        values.extend(admin['groups'])
    return db.execute("SELECT e.*,d.name AS device_name,CASE WHEN e.kind='closed' THEN e.occurred-(SELECT MIN(a.occurred) FROM connection_events a WHERE a.device=e.device AND a.session_id=e.session_id AND a.group_id=e.group_id AND a.kind='authorized' AND a.occurred<=e.occurred) END AS duration_seconds FROM connection_events e JOIN devices d ON d.id=e.device WHERE "
                      + ' AND '.join(clauses) + ' ORDER BY e.id DESC LIMIT ?', (*values, limit)).fetchall()


def router(store, require, device_auth, effective_policy):
    routes = APIRouter()

    @routes.post('/api/agent/events')
    def ingest(body: EventBatch, device=Depends(device_auth)):
        now = int(time.time())
        if any(e.occurred > now + 300 or e.occurred < now - 90 * 86400 for e in body.events):
            raise HTTPException(422, 'Event timestamp outside accepted range')
        with store.connect() as db:
            for event in body.events:
                db.execute('INSERT OR IGNORE INTO connection_events(event_id,device,group_id,session_id,kind,occurred,received,peer_id,peer_name,peer_ip,connection_type) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                           (device['id'] + ':' + event.event_id, device['id'], device['group_id'], event.session_id,
                            event.kind, event.occurred, now, event.peer_id, event.peer_name, event.peer_ip, event.connection_type))
        return {'accepted': len(body.events)}

    @routes.get('/api/connections')
    def connections(device_id: str = '', days: int = Query(30, ge=1, le=90),
                    before: int = 9223372036854775807, admin=Depends(require('audit.read'))):
        with store.connect() as db:
            rows = scoped_events(db, admin, device_id, days, before)
        return {'events': [dict(r) for r in rows], 'next_before': rows[-1]['id'] if len(rows) == 200 else None,
                'identity_source': 'Peer ID and name are reported by the remote client; they are not a verified panel administrator identity.'}

    @routes.get('/api/devices/{identifier}')
    def detail(identifier: str, admin=Depends(require('devices.read'))):
        with store.connect() as db:
            device = device_in_scope(db, admin, identifier)
            device.pop('token', None)
            row = db.execute('SELECT * FROM device_details WHERE device=?', (identifier,)).fetchone()
            policy = effective_policy(db, device)
            policy['has_password'] = policy.pop('password') is not None
            events = scoped_events(db, admin, identifier, limit=20) if 'audit.read' in json.loads(admin['permissions']) else []
        return {'device': device, 'details': dict(row) if row else {}, 'policy': policy,
                'events': [dict(r) for r in events], 'online': device['active'] == 1 and int(time.time()) - device['last_seen'] < 150}

    @routes.post('/api/devices/{identifier}/connect')
    def connect(identifier: str, admin=Depends(require('devices.connect'))):
        with store.connect() as db:
            device = device_in_scope(db, admin, identifier)
            if not device['active'] or not re.fullmatch(r'[A-Za-z0-9_-]{3,50}', device['rustdesk_id']):
                raise HTTPException(409, 'Device has no active usable connection ID')
            store.audit(db, admin['username'], 'connection.launch_requested', identifier, device['group_id'])
        return {'url': 'bamdaddesk://' + device['rustdesk_id']}

    @routes.get('/api/dashboard')
    def dashboard(admin=Depends(require('devices.read'))):
        now = int(time.time())
        with store.connect() as db:
            devices = [dict(r) for r in db.execute('SELECT id,name,group_id,version,last_seen,applied,error,active FROM devices') if group_allowed(admin, r['group_id'])]
            groups = [dict(r) for r in db.execute('SELECT * FROM groups') if group_allowed(admin, r['id'])]
            revision = db.execute("SELECT value FROM meta WHERE key='revision'").fetchone()[0]
            # Aggregation uses all matching events, never the paginated log page.
            clauses, values = ['e.occurred>=?', "e.kind='authorized'"], [now - 14 * 86400]
            if admin['groups'] is not None:
                marks = ','.join('?' for _ in admin['groups']) or 'NULL'
                clauses.extend([f'e.group_id IN ({marks})', f'd.group_id IN ({marks})'])
                values.extend(admin['groups']); values.extend(admin['groups'])
            daily = []
            if 'audit.read' in json.loads(admin['permissions']):
                daily = [dict(r) for r in db.execute("SELECT strftime('%Y-%m-%d',e.occurred,'unixepoch') AS day,COUNT(*) AS count FROM connection_events e JOIN devices d ON d.id=e.device WHERE " + ' AND '.join(clauses) + ' GROUP BY day ORDER BY day', values)]
        versions = {}
        for device in devices:
            version = device['version'] or 'Unknown'
            versions[version] = versions.get(version, 0) + 1
        return {'total': len(devices), 'online': sum(d['active'] and now-d['last_seen'] < 150 for d in devices),
                'pending': sum(d['active'] and d['applied'] < revision for d in devices),
                'errors': sum(bool(d['error']) for d in devices), 'versions': versions, 'daily': daily,
                'groups': [{'name': g['name'], 'count': sum(d['group_id'] == g['id'] for d in devices)} for g in groups],
                'timezone': 'UTC', 'can_read_connections': 'audit.read' in json.loads(admin['permissions'])}

    return routes
