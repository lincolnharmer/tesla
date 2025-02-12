import requests
import hashlib
import base64
import urllib
import json
import datetime
import getpass

from random import choice
from string import hexdigits

email = input('email: ')
password = getpass.getpass('password: ')
passcode = input('passcode: ')

# Step 1: Obtain the login page
code_verifier = ''.join(choice(hexdigits) for i in range(86))
print('code: ' + code_verifier)

code_challenge = base64.b64encode(
  hashlib.sha256(
    code_verifier.encode('utf-8')
  ).digest()
).decode()
print('challenge: ' + code_challenge)

url = ('https://auth.tesla.com/oauth2/v3/authorize'
       + '?client_id=ownerapi'
       + '&code_challenge=' 
       + code_challenge
       + '&code_challenge_method=S256'
       + '&redirect_uri=' 
       + urllib.parse.quote('https://auth.tesla.com/void/callback')
       + '&response_type=code'
       + '&scope=' 
       + urllib.parse.quote('openid email offline_access')
       + '&state=state')

print('url: ' + url)

response = requests.get(url)
#print(response.content)

csrf = response.content[
         response.content.decode('utf-8').find('name="_csrf"') + 20: 
         response.content.decode('utf-8').find('name="_csrf"') + 56
       ]
phase = response.content[
          response.content.decode('utf-8').find('name="_phase"') + 21: 
          response.content.decode('utf-8').find('name="_phase"') + 33
        ]
process = response.content[
            response.content.decode('utf-8').find('name="_process"') + 23: 
            response.content.decode('utf-8').find('name="_process"') + 24
          ]
transaction_id = response.content[
                   response.content.decode('utf-8').find('name="transaction_id"') + 29: 
                   response.content.decode('utf-8').find('name="transaction_id"') + 37
                 ].decode()
cookie = response.headers.get('Set-Cookie')

#print('csrf: ' + csrf)
#print('phase: ' + phase)
#print('process: ' + process)
print('trasaction_id: ' + transaction_id)
print('cookie: ' + cookie)

# Step 2: Authenticate user name and password
payload = {
  '_csrf': csrf,
  '_phase': phase,
  '_process': process,
  'transaction_id': transaction_id,
  'cancel': '',
  'identity': email,
  'credential': password
}

response = requests.post(
             url, 
             data=payload, 
             headers={'Cookie': cookie}
           )

# Step 3: Authenticate MFA
url =  ('https://auth.tesla.com/oauth2/v3/authorize/mfa/factors'
        + '?transaction_id=' 
        + transaction_id)

response = requests.get(url, headers={'Cookie': cookie})

url = 'https://auth.tesla.com/oauth2/v3/authorize/mfa/verify'
#print('factor_id: ' + json.loads(response.text)['data'][0]['id'])
payload = {
  'factor_id': json.loads(response.text)['data'][0]['id'],
  'transaction_id': transaction_id,
  'passcode': passcode
}

response = requests.post(
             url, 
             json=payload, 
             headers={'Cookie': cookie}
           )

# Step 4: Obtain an authorization code
url = ('https://auth.tesla.com/oauth2/v3/authorize'
        + '?client_id=ownerapi'
        + '&code_challenge=' 
        + code_challenge
        + '&code_challenge_method=S256'
        + '&redirect_uri=' 
        + urllib.parse.quote('https://auth.tesla.com/void/callback')
        + '&response_type=code'
        + '&scope=' 
        + urllib.parse.quote('openid email offline_access')
        + '&state=state')
payload = {
  'transaction_id': transaction_id
}

response = requests.post(
             url, 
             data=payload, 
             allow_redirects=False, 
             headers={'Cookie': cookie}
           )

code = response.content[
         response.content.decode('utf-8').find('code') + 5: 
         response.content.decode('utf-8').find('&')
       ].decode()
print('code: ' + code)

# Step 5: Exchange authorization code for bearer token
url = 'https://auth.tesla.com/oauth2/v3/token'
payload = {
  'grant_type': 'authorization_code',
  'client_id': 'ownerapi',
  'code': code,
  'code_verifier': code_verifier,
  'redirect_uri': 'https://auth.tesla.com/void/callback'
}

response = requests.post(
             url, 
             json=payload, 
             headers={'Cookie': cookie}
           )

# Step 6: Exchange bearer token for access token
url = 'https://owner-api.teslamotors.com/oauth/token'
payload = {
  'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
  'client_id': '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384',
  'client_secret': 'c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3'
}

response = requests.post(
             url, 
             json=payload, 
             headers={'authorization': 'Bearer ' 
                      + json.loads(response.text)['access_token']}
           ) 

print('# access_token=' + json.loads(response.text)['access_token'])
print(
  '# expires_at: ' 
  + str(
    datetime.datetime.fromtimestamp(
      json.loads(response.text)['created_at'] 
      + json.loads(response.text)['expires_in']
    )
  )
)
print('# refresh_token: ' + json.loads(response.text)['refresh_token'])
print(
  '# created_at: ' 
  + str(
    datetime.datetime.fromtimestamp(
      json.loads(response.text)['created_at']
    )
  )
)

