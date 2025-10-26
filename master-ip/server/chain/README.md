bash

## RUN APP:  
~~~
PYTHONPATH=.. uvicorn app.main:app --reload --port 8000
~~~

## To Create keys (inside master-ip/server/chain/keys)
~~~

openssl ecparam -name prime256v1 -genkey -noout -out sign_priv.pem
openssl ec -in sign_priv.pem -pubout -out sign_pub.pem

~~~
## Set below in your .env

~~~
SIGNER_KEY_PATH=<absolute_path_of_sign_priv.pem>
PLATFORM_PUBKEY_PATH=<absolute_path_of_sign_pub.pem>
~~~

## To Create

~~~
curl -sS -X POST "http://localhost:8000/create" \
  -H "Content-Type: application/json" \
  -d '{"artisan":{"name":"Ravi Verma","location":"Mithila, Bihar","contact_number":"9876543210","email":"ravi@example.com","aadhaar_number":"1234-5678-9101"},"art":{"name":"Madhubani Painting","description":"Traditional artwork depicting rural folklore","photo_url":"https://cdn.example.com/img123.jpg"}}' | jq
~~~


## To Anchor (from server)

~~~
python -m chain.batcher
~~~


## To Verify

~~~
curl -s http://localhost:8000/verify/<craft-id> | python3 -m json.tool
~~~

## To verify on internet 

~~~
https://amoy.polygonscan.com/tx/0x<TX_HASH>
~~~

