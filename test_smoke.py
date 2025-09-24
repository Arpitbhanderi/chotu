from app import app
client = app.test_client()
import json

resp1 = client.post('/api/chat', json={'message': 'make an invoice for arpit', 'history': []})
print('1:', resp1.status_code)
print('1b:', resp1.json)

resp2 = client.post('/api/chat', json={'message': 'he purchased LED TV worth 10900', 'history': resp1.json.get('conversation_context', [])})
print('2:', resp2.status_code)
print('2b:', resp2.json)