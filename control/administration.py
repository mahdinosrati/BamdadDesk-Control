"""Group and enrollment lifecycle operations; never return enrollment secrets."""
import json
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .scopes import group_allowed, policy_in_scope, require_global, require_group


class GroupEdit(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=100)


class GroupRemoval(BaseModel):
    model_config = ConfigDict(extra='forbid')
    destination: str = Field(max_length=40)


class TokenEdit(BaseModel):
    model_config = ConfigDict(extra='forbid')
    label: str = Field(min_length=1, max_length=100)
    group_id: str = Field(default='', max_length=40)
    hours: int | None = Field(default=None, ge=1, le=8760)
    remaining: int = Field(ge=0, le=10000)


def router(store, require, group_exists):
    routes = APIRouter()

    @routes.put('/api/groups/{identifier}')
    def edit_group(identifier: str, body: GroupEdit, admin=Depends(require('devices.write'))):
        require_group(admin, identifier)
        name = body.name.strip()
        if not name:
            raise HTTPException(422, 'Group name cannot be blank')
        with store.connect() as db:
            group_exists(db, identifier)
            if not identifier:
                raise HTTPException(404, 'Group not found')
            if db.execute('SELECT 1 FROM groups WHERE name=? AND id!=?', (name, identifier)).fetchone():
                raise HTTPException(409, 'Group already exists')
            db.execute('UPDATE groups SET name=? WHERE id=?', (name, identifier))
            store.audit(db, admin['username'], 'group.rename', identifier, identifier)
        return {'ok': True}

    @routes.post('/api/groups/{identifier}/remove')
    def remove_group(identifier: str, body: GroupRemoval, admin=Depends(require('devices.write'))):
        require_global(admin)
        if not identifier or identifier == body.destination:
            raise HTTPException(422, 'Choose a different destination for existing devices')
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            group_exists(db, identifier)
            group_exists(db, body.destination)
            db.execute('UPDATE devices SET group_id=? WHERE group_id=?', (body.destination, identifier))
            # Tokens retain their original scope and are revoked rather than silently moved.
            db.execute('UPDATE enrollment_details SET revoked=1 WHERE token IN (SELECT token FROM enrollments WHERE group_id=?)', (identifier,))
            db.execute('UPDATE enrollments SET remaining=0 WHERE group_id=?', (identifier,))
            for row in db.execute('SELECT * FROM admin_scopes').fetchall():
                values = json.loads(row['groups_json'])
                if identifier in values:
                    db.execute('UPDATE admin_scopes SET groups_json=? WHERE admin=?', (json.dumps([g for g in values if g != identifier]), row['admin']))
            db.execute('DELETE FROM policies WHERE scope=?', ('group:' + identifier,))
            db.execute('DELETE FROM groups WHERE id=?', (identifier,))
            store.bump(db)
            store.audit(db, admin['username'], 'group.remove', identifier, identifier)
        return {'ok': True}

    @routes.get('/api/enrollments')
    def list_tokens(admin=Depends(require('enrollment.write'))):
        now = int(time.time())
        with store.connect() as db:
            rows = db.execute('SELECT m.id,e.label,e.group_id,e.expires,e.remaining,m.created,m.used,m.revoked FROM enrollments e JOIN enrollment_details m ON m.token=e.token ORDER BY m.created DESC,m.id')
            return [{**dict(r), 'status': 'revoked' if r['revoked'] else 'expired' if r['expires'] <= now else 'exhausted' if r['remaining'] == 0 else 'active'} for r in rows if group_allowed(admin, r['group_id'])]

    def token_row(db, identifier, admin):
        row = db.execute('SELECT e.*,m.revoked FROM enrollments e JOIN enrollment_details m ON m.token=e.token WHERE m.id=?', (identifier,)).fetchone()
        if not row:
            raise HTTPException(404, 'Token not found')
        require_group(admin, row['group_id'])
        return row

    @routes.put('/api/enrollments/{identifier}')
    def edit_token(identifier: str, body: TokenEdit, admin=Depends(require('enrollment.write'))):
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = token_row(db, identifier, admin)
            if row['revoked']:
                raise HTTPException(409, 'Revoked tokens cannot be reactivated; create a replacement')
            require_group(admin, body.group_id)
            group_exists(db, body.group_id)
            if not body.label.strip():
                raise HTTPException(422, 'Token label cannot be blank')
            expires = int(time.time()) + body.hours * 3600 if body.hours is not None else row['expires']
            db.execute('UPDATE enrollments SET label=?,group_id=?,expires=?,remaining=? WHERE token=?', (body.label.strip(), body.group_id, expires, body.remaining, row['token']))
            store.audit(db, admin['username'], 'enrollment.update', identifier, row['group_id'])
        return {'ok': True}

    @routes.post('/api/enrollments/{identifier}/revoke')
    def revoke_token(identifier: str, admin=Depends(require('enrollment.write'))):
        with store.connect() as db:
            row = token_row(db, identifier, admin)
            db.execute('UPDATE enrollments SET remaining=0 WHERE token=?', (row['token'],))
            db.execute('UPDATE enrollment_details SET revoked=1 WHERE id=?', (identifier,))
            store.audit(db, admin['username'], 'enrollment.revoke', identifier, row['group_id'])
        return {'ok': True}

    @routes.get('/api/password-source/{scope}')
    def password_source(scope: str, admin=Depends(require('policies.write'))):
        with store.connect() as db:
            group = policy_in_scope(db, admin, scope)
            scopes = ['global']
            if group:
                scopes.append('group:' + group)
            if scope.startswith('device:'):
                scopes.append(scope)
            source = 'client-default'
            for candidate in scopes:
                row = db.execute('SELECT password FROM policies WHERE scope=?', (candidate,)).fetchone()
                if row and row['password'] is not None:
                    source = candidate
        return {'source': source, 'recoverable': False}

    return routes
