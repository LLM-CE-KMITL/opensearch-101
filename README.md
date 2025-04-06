# opensearch-101
For learning Opensearch

## Run Docker Compose
1.  Create a file named "**.env**"  having admin password
   
```
export OPENSEARCH_INITIAL_ADMIN_PASSWORD=PassWord.1234
```

2.  Run
   
```
docker compose up -d
```

**Ref:**
* https://opensearch.org/docs/latest/install-and-configure/install-opensearch/docker/#sample-docker-composeyml

## For the Python Code

1. Adding Certificate
    https://opensearch.org/docs/latest/security/configuration/generate-certificates/

```
openssl genrsa -out root-ca-key.pem 2048
openssl req -new -x509 -sha256 -key root-ca-key.pem -out root-ca.pem -days 730
```

2. Edit Config Variables in the **opensearch-code.py**, For example

```
HOST = 'localhost'
PORT = 9200
USERNAME = 'admin'
PASSWORD = 'PassWord.1234'
CA_CERTS_PATH = 'PATH/TO/root-ca.pem'
```
