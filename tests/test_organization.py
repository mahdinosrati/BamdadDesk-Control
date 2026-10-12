from test_control import panel, enroll, verify
from control.storage import digest


def test_organization_settings_and_signed_management_address(panel):
    client, store = panel
    assert client.put('/api/organization', json={'api_url': 'http://example.com'}).status_code == 422
    assert client.put('/api/organization', json={'api_url': 'https://example.com:8443/', 'automatic_enrollment': True}).status_code == 200
    device, _ = enroll(client)
    response = client.get('/api/agent/management', headers={'Authorization': 'Bearer ' + device['token']})
    assert verify(response.json(), store) == {'schema': 1, 'device_id': device['device_id'], 'api_url': 'https://example.com:8443'}


def test_switch_stops_new_automatic_enrollment_without_stopping_existing_devices(panel):
    client, store = panel
    device, _ = enroll(client)
    grant = client.post('/api/enrollments', json={'label': 'installer', 'uses': 2}).json()['token']
    with store.connect() as db:
        db.execute('INSERT INTO automatic_enrollments VALUES (?)', (digest(grant),))
    body = {'token': grant, 'name': 'Workstation', 'version': '1.6.0'}
    assert client.post('/api/agent/enroll', json=body).status_code == 403
    assert client.put('/api/organization', json={'api_url': 'https://example.com', 'automatic_enrollment': True}).status_code == 200
    assert client.post('/api/agent/enroll', json=body).status_code == 200
    assert client.put('/api/organization', json={'api_url': 'https://example.com', 'automatic_enrollment': False}).status_code == 200
    assert client.post('/api/agent/enroll', json=body).status_code == 403
    assert client.get('/api/agent/management', headers={'Authorization': 'Bearer ' + device['token']}).status_code == 200
