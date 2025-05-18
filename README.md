# opensearch-101
For learning Opensearch

## Run Docker Compose
1.  Create a data folder named "**opensearch-data1**"  
   
```
mkdir opensearch-data1
```

2.  Run
   
```
docker run -it -p 9200:9200 -p 9600:9600 -e OPENSEARCH_INITIAL_ADMIN_PASSWORD=@PassWord.1234 -e "discovery.type=single-node" -e "DISABLE_SECURITY_PLUGIN=true" -v opensearch-data1:/usr/share/opensearch/data  --name opensearch-node opensearchproject/opensearch:latest
```


## For the Python Code

1. Edit Config Variables in the **opensearch-code.py**, For example

```
HOST = 'localhost'
PORT = 9200
USERNAME = 'admin'
PASSWORD = '@PassWord.1234'
```
