import shutil

import pytest

from test_control import panel


@pytest.mark.skipif(not shutil.which('makensis'), reason='NSIS compiler is tested in Linux CI')
def test_download_compiles_executable_and_registers_limited_grant(panel):
    client, store = panel
    executable = b'MZ' + bytes(1024)
    release = client.post('/api/releases?version=1.7.0', files={'file': ('BamdadDesk.exe', executable, 'application/octet-stream')})
    assert release.status_code == 200, release.text
    identifier = client.get('/api/releases').json()[0]['id']
    client.put('/api/organization', json={'api_url': 'https://desk.example.com', 'automatic_enrollment': True})
    response = client.post('/api/organization/installer', json={'label': 'IT package', 'release_id': identifier, 'uses': 3})
    assert response.status_code == 200, response.text[:500]
    assert response.content[:2] == b'MZ'
    assert response.headers['cache-control'] == 'no-store'
    token = client.get('/api/enrollments').json()[0]
    assert token['label'] == 'IT package' and token['remaining'] == 3
    assert not list((store.directory / 'packages').iterdir())
