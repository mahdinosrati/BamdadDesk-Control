import time

from fastapi.testclient import TestClient
from test_control import panel, enroll, heartbeat


def sign_in(app, username):
    client = TestClient(app)
    response = client.post('/api/login', json={'username': username, 'password': 'branch-test-password'})
    client.headers['x-csrf-token'] = response.json()['csrf']
    return client


def test_group_boundaries_cover_lists_direct_ids_policies_and_escalation(panel):
    client, _ = panel
    a = client.post('/api/groups', json={'name': 'Branch A'}).json()['id']
    b = client.post('/api/groups', json={'name': 'Branch B'}).json()['id']
    da, _ = enroll(client, group_id=a)
    db, _ = enroll(client, group_id=b)
    permissions = ['devices.read', 'devices.write', 'devices.connect', 'policies.write', 'audit.read', 'enrollment.write']
    created = client.post('/api/admins', json={'username': 'branch', 'password': 'branch-test-password', 'permissions': permissions, 'groups': [a]})
    assert created.status_code == 200
    scoped = sign_in(client.app, 'branch')
    assert [r['id'] for r in scoped.get('/api/devices').json()['devices']] == [da['device_id']]
    assert [r['id'] for r in scoped.get('/api/groups').json()] == [a]
    assert scoped.get('/api/devices/' + db['device_id']).status_code == 404
    assert scoped.put('/api/devices/' + da['device_id'], json={'group_id': b}).status_code == 404
    assert scoped.post('/api/enrollments', json={'label': 'escape', 'group_id': b}).status_code == 404
    assert scoped.post('/api/groups', json={'name': 'escape'}).status_code == 403
    assert scoped.get('/api/policies/global').status_code == 403
    assert scoped.get('/api/policies/group:' + b).status_code == 404
    assert scoped.get('/api/policies/device:' + db['device_id']).status_code == 404
    assert scoped.get('/api/admins').status_code == 403
    assert scoped.post('/api/devices/' + db['device_id'] + '/connect', json={}).status_code == 404
    assert all(r['group_id'] == a for r in scoped.get('/api/audit').json())
    assert client.post('/api/admins', json={'username': 'escape', 'password': 'branch-test-password', 'permissions': ['admins.write'], 'groups': [a]}).status_code == 422
    assert client.put('/api/admins/' + created.json()['id'], json={'permissions': permissions, 'active': True}).status_code == 200
    assert next(r for r in client.get('/api/admins').json() if r['id'] == created.json()['id'])['groups'] == [a]


def test_real_events_are_deduplicated_scoped_and_device_details_are_redacted(panel):
    client, _ = panel
    group = client.post('/api/groups', json={'name': 'Support'}).json()['id']
    device, _ = enroll(client, group_id=group)
    assert heartbeat(client, device['token'], rustdesk_id='123456789', platform='windows x86_64', username='ExampleUser').status_code == 200
    now = int(time.time())
    event = {'event_id': 'test-event-identifier-1234', 'session_id': 'test-session-1234', 'kind': 'authorized', 'occurred': now, 'peer_id': '987654321', 'peer_name': 'Reported peer', 'connection_type': 0}
    headers = {'Authorization': 'Bearer ' + device['token']}
    for _ in range(2):
        assert client.post('/api/agent/events', headers=headers, json={'events': [event]}).status_code == 200
    events = client.get('/api/connections').json()['events']
    assert len(events) == 1 and events[0]['peer_name'] == 'Reported peer'
    assert client.get('/api/dashboard').json()['daily'][0]['count'] == 1
    assert events[0]['duration_seconds'] is None
    close = {**event, 'event_id': 'closed-event-identifier-1234', 'kind': 'closed', 'occurred': now + 45}
    assert client.post('/api/agent/events', headers=headers, json={'events': [close]}).status_code == 200
    assert client.get('/api/connections').json()['events'][0]['duration_seconds'] == 45
    assert client.post('/api/agent/events', headers=headers, json={'events': [{**event, 'device': 'spoof'}]}).status_code == 422
    assert client.post('/api/agent/events', headers=headers, json={'events': [{**event, 'occurred': now + 600}]}).status_code == 422
    details = client.get('/api/devices/' + device['device_id']).json()
    assert details['details']['username'] == 'ExampleUser'
    assert 'token' not in details['device'] and 'password' not in details['policy']
    assert client.post('/api/devices/' + device['device_id'] + '/connect', json={}).json()['url'] == 'bamdaddesk://123456789'
    assert client.put('/api/devices/' + device['device_id'], json={'group_id': group, 'alias': 'Front desk', 'note': 'IT asset'}).status_code == 200
    assert client.get('/api/devices/' + device['device_id']).json()['details']['alias'] == 'Front desk'
    assert client.post('/api/admins', json={'username': 'isolated', 'password': 'branch-test-password', 'permissions': ['devices.read', 'audit.read'], 'groups': []}).status_code == 200
    isolated = sign_in(client.app, 'isolated')
    assert isolated.get('/api/connections').json()['events'] == []
    assert isolated.get('/api/dashboard').json()['total'] == 0
    assert isolated.get('/api/dashboard').json()['daily'] == []

def test_existing_audit_database_is_upgraded_without_losing_history(tmp_path):
    import sqlite3
    from control.storage import Store
    database = tmp_path / 'control.sqlite3'
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE audit (id INTEGER PRIMARY KEY,created INTEGER NOT NULL,actor TEXT NOT NULL,action TEXT NOT NULL,target TEXT NOT NULL)')
        db.execute("INSERT INTO audit VALUES (1,100,'owner','login','owner')")
    store = Store(tmp_path)
    with store.connect() as db:
        row = dict(db.execute('SELECT * FROM audit WHERE id=1').fetchone())
        assert row == {'id': 1, 'created': 100, 'actor': 'owner', 'action': 'login', 'target': 'owner', 'group_id': ''}
        store.audit(db, 'owner', 'device.update', 'example', 'branch-a')
        assert db.execute('SELECT group_id FROM audit WHERE id=2').fetchone()[0] == 'branch-a'
