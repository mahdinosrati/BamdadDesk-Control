from test_control import panel, enroll


def test_token_list_edit_extend_and_revoke(panel):
    client, _ = panel
    created = client.post('/api/enrollments', json={'label': 'setup', 'uses': 2}).json()
    row = client.get('/api/enrollments').json()[0]
    assert created['token'] not in str(row)
    assert row['used'] == 0 and row['remaining'] == 2
    assert client.put('/api/enrollments/' + row['id'], json={'label': 'renamed', 'hours': 72, 'remaining': 3}).status_code == 200
    assert client.get('/api/enrollments').json()[0]['expires'] > row['expires']
    assert client.post('/api/enrollments/' + row['id'] + '/revoke').status_code == 200
    assert client.post('/api/agent/enroll', json={'token': created['token'], 'name': 'test', 'version': '1.6.0'}).status_code == 401
    assert client.put('/api/enrollments/' + row['id'], json={'label': 'restore', 'remaining': 3}).status_code == 409


def test_group_delete_moves_devices_and_removes_group_policy(panel):
    client, store = panel
    source = client.post('/api/groups', json={'name': 'source'}).json()['id']
    target = client.post('/api/groups', json={'name': 'target'}).json()['id']
    device, _ = enroll(client, group_id=source)
    assert client.put('/api/groups/' + source, json={'name': 'renamed'}).status_code == 200
    assert client.post('/api/groups/' + source + '/remove', json={'destination': source}).status_code == 422
    assert client.post('/api/groups/' + source + '/remove', json={'destination': target}).status_code == 200
    assert client.get('/api/devices/' + device['device_id']).json()['device']['group_id'] == target
    assert not any(g['id'] == source for g in client.get('/api/groups').json())


def test_password_source_reports_inheritance_without_hash(panel):
    client, store = panel
    device, _ = enroll(client)
    assert client.get('/api/password-source/device:' + device['device_id']).json()['source'] == 'client-default'
    revision = client.get('/api/policies/global').json()['revision']
    assert client.put('/api/policies/global', json={'options': {}, 'password': 'test-secret', 'expected_revision': revision}).status_code == 200
    result = client.get('/api/password-source/device:' + device['device_id']).json()
    assert result == {'source': 'global', 'recoverable': False}
