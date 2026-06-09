import pytest
import json
from src.ui.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_cocktails(client):
    rv = client.get('/api/cocktails')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'cocktails' in data
    assert isinstance(data['cocktails'], list)

def test_get_bars(client):
    rv = client.get('/api/bars')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'bars' in data
    assert isinstance(data['bars'], list)

def test_chat_endpoint_missing_message(client):
    rv = client.post('/api/chat', json={})
    assert rv.status_code == 400
    data = json.loads(rv.data)
    assert 'error' in data
