import time

from test_control import panel, enroll


def test_filtered_report_and_csv_cover_all_matches(panel):
    client, store = panel
    device, _ = enroll(client)
    now = int(time.time())
    with store.connect() as db:
        for i in range(105):
            db.execute('INSERT INTO connection_events(event_id,device,group_id,session_id,kind,occurred,received,peer_id,peer_name,peer_ip,connection_type) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                       (str(i), device['device_id'], '', str(i), 'authorized', now, now, 'peer', '=malicious-formula', '192.0.2.1', 0))
    data = client.get('/api/reports/connections?search=malicious&kind=authorized').json()
    assert data['summary']['events'] == 105 and len(data['events']) == 100 and data['pages'] == 2
    assert len(client.get('/api/reports/connections?page=2').json()['events']) == 5
    exported = client.get('/api/reports/connections?export=true').text
    assert exported.count("'=malicious-formula") == 105
    assert client.get('/api/reports/connections?start=2030-01-02&end=2030-01-01').status_code == 422


def test_admin_creation_returns_clear_validation_and_duplicate_errors(panel):
    client, store = panel
    body = {'username': 'helpdesk', 'password': 'short', 'permissions': ['devices.read']}
    assert client.post('/api/admins', json=body).status_code == 422
    body['password'] = 'test-helpdesk-password'
    assert client.post('/api/admins', json=body).status_code == 200
    duplicate = client.post('/api/admins', json=body)
    assert duplicate.status_code == 409 and duplicate.json()['detail'] == 'Username already exists'
