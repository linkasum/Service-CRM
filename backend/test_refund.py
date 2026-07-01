#!/usr/bin/env python3
import http.client, json
conn = http.client.HTTPConnection('127.0.0.1', 8000)
conn.request('POST', '/api/auth/login', body=json.dumps({'username':'admin','password':'admin'}), headers={'Content-Type': 'application/json'})
token = json.loads(conn.getresponse().read().decode())['access_token']
conn.close()
conn = http.client.HTTPConnection('127.0.0.1', 8000)
conn.request('POST', '/api/payments/', body=json.dumps({'order_id':14,'payment_type':'refund','amount':'500','method':'cash'}), headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
resp = conn.getresponse()
print(f"Status: {resp.status}, Response: {resp.read().decode()[:200]}")
conn.close()
