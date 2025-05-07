# -*- coding: utf-8 -*-
import numpy as np


from opensearchpy import OpenSearch, helpers
#from langchain_community.vectorstores import OpenSearchVectorSearch

from transformers import AutoTokenizer, AutoModel
import torch

#import deepcut

######## Get Vector Embeding ##############

#em_name = "BAAI/bge-m3"
EM_NAME = "BAAI/bge-reranker-v2-m3"  #smaller model
em_tokenizer = AutoTokenizer.from_pretrained(EM_NAME)
em_model = AutoModel.from_pretrained(EM_NAME)


######## Embeding Function ##############


def get_embedding(text):
    inputs = em_tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        outputs = em_model(**inputs)
    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    return embedding / np.linalg.norm(embedding)


######## Doc ##############


'''
- Open Search Docker
    https://opensearch.org/docs/latest/install-and-configure/install-opensearch/docker/#sample-docker-composeyml

- Certificate
    https://opensearch.org/docs/latest/security/configuration/generate-certificates/

- Coding
    https://python.langchain.com/docs/integrations/vectorstores/opensearch/
'''

######## Connect OpenSearch ##############

# config

HOST = 'localhost'
PORT = 9200
USERNAME = 'admin'
PASSWORD = '{PASSSWORD}'
CA_CERTS_PATH = 'PATH/TO/root-ca.pem'

# connect

client = OpenSearch(
            hosts=[ {'host': HOST, 'port': PORT}],
            http_compress=True,
            http_auth=(USERNAME, PASSWORD),
            use_ssl=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            ca_certs=CA_CERTS_PATH
        )

# Print out a debug print to see if connection is successful
print( client.info() )


######## Create Index ##############

# index is like a DB or vector space
INDEX_NAME = "rc_index"

'''
# to delete the existing index
response = client.indices.delete( index = index_name )
'''

# Create index with dense vector mapping
if not client.indices.exists(index=INDEX_NAME):

    index_body = {
        "settings": {
            "index": {
                "knn": True
            }
        },
        "mappings": {
            "properties": {
                "text": {"type": "text"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 1024,  #size of BGE
                    "method": {
                        "name": "hnsw",
                        "engine": "faiss", # nmslib
                        "space_type": "cosinesimil"
                    }
                }
            }
        }
    }

    
    response = client.indices.create(INDEX_NAME, body=index_body)
    print(f"Index '{INDEX_NAME}' created.")
else:
    print(f"Index '{INDEX_NAME}' already exists.")
    
    
    
######## Adding 1 Entry ##############


text = "OpenSearch with BGE-M3 embedding example."

doc = {
    "text": text,
    "embedding": get_embedding(text).tolist()
}

response = client.index(index=INDEX_NAME, body=doc)
print(f"Document indexed with ID: {response['_id']}")


######## Query ##############



query = "example"
query_vector = get_embedding(query).tolist()

query_body = {
    "size": 5,
    "query": {
        "knn": {
            "embedding": {
                "vector": query_vector,
                "k": 5  # คืนผลลัพธ์ 5 อันดับแรก
            }
        }
    }
}

response = client.search(index=INDEX_NAME, body=query_body)
for hit in response['hits']['hits']:
    print(f"Score: {hit['_score']:.4f}, Text: {hit['_source']['text']}")



######## Bulk Store ##############



texts = [
    { "text": "ตู้เย็นแบบสองประตูเหมาะสำหรับครอบครัวขนาดกลางถึงใหญ่ มีช่องแช่แข็งแยกออกจากช่องแช่เย็น ทำให้ง่ายต่อการจัดเก็บอาหารสดและอาหารแช่แข็งอย่างเป็นระเบียบ และยังช่วยลดกลิ่นปะปนกันภายในตู้.",
      "doc": "device" },
    { "text": "เครื่องซักผ้าฝาหน้าถูกออกแบบมาให้ประหยัดพลังงานและน้ำ พร้อมระบบหมุนปั่นที่มีประสิทธิภาพสูง สามารถขจัดคราบฝังลึกได้อย่างหมดจด เหมาะสำหรับการใช้งานในครัวเรือนที่ต้องการประสิทธิภาพการซักที่ดีเยี่ยม.",
      "doc": "device" },
    { "text": "ไมโครเวฟแบบดิจิทัลช่วยให้การอุ่นอาหารเป็นเรื่องง่ายและรวดเร็ว มาพร้อมฟังก์ชันละลายน้ำแข็งอัตโนมัติและโปรแกรมทำอาหารหลากหลาย ทำให้เหมาะกับผู้ที่มีเวลาจำกัดในการทำอาหารแต่ยังต้องการความสะดวกสบาย.",
      "doc": "device" },
    { "text": "เครื่องปรับอากาศแบบติดผนังสามารถควบคุมอุณหภูมิและความชื้นในห้องได้อย่างมีประสิทธิภาพ พร้อมระบบฟอกอากาศในตัว ช่วยกรองฝุ่นละอองและกลิ่นไม่พึงประสงค์ เหมาะสำหรับใช้ในห้องนอนหรือห้องนั่งเล่น.",
      "doc": "device" },
    { "text": "หม้อหุงข้าวไฟฟ้ามาพร้อมเทคโนโลยีควบคุมความร้อนอัจฉริยะ ทำให้ข้าวสุกทั่วถึง นุ่ม และหอมทุกเม็ด นอกจากนี้ยังมีโหมดการหุงสำหรับข้าวกล้อง โจ๊ก และการอุ่นอัตโนมัติ เหมาะกับทุกครอบครัว.",
      "doc": "device" },
    
    { "text": "ข้าวมันไก่เป็นอาหารจานเดียวที่ได้รับความนิยมอย่างแพร่หลาย ประกอบด้วยข้าวที่หุงด้วยน้ำซุปไก่จนมีกลิ่นหอม เสิร์ฟคู่กับไก่ต้มเนื้อนุ่ม น้ำจิ้มรสจัด และน้ำซุปใสร้อน ๆ ถือเป็นเมนูที่อร่อยและอิ่มท้องในราคาย่อมเยา.",
      "doc": "food" },
    { "text": "ต้มยำกุ้งเป็นอาหารไทยที่มีรสชาติจัดจ้านและกลิ่นหอมของสมุนไพรสด เช่น ตะไคร้ ใบมะกรูด และข่า จุดเด่นคือความเปรี้ยวจากมะนาวและเผ็ดจากพริกขี้หนู รสชาติกลมกล่อมเมื่อทานกับข้าวสวยร้อน ๆ.",
      "doc": "food" },
    { "text": "ผัดไทยเป็นอาหารจานเดียวที่มีต้นกำเนิดจากอาหารริมทางในประเทศไทย เส้นจันท์ผัดกับน้ำปรุงรสเข้มข้น ใส่กุ้ง เต้าหู้ และไข่ โรยด้วยถั่วลิสงบด เสิร์ฟพร้อมถั่วงอกและมะนาว เหมาะกับทั้งคนไทยและนักท่องเที่ยว.",
      "doc": "food" },
    { "text": "แกงเขียวหวานไก่เป็นเมนูแกงไทยที่มีกลิ่นหอมเฉพาะตัวจากพริกแกงเขียวหวานและกะทิ รสชาติกลมกล่อม หวานมัน และเผ็ดเล็กน้อย นิยมรับประทานคู่กับข้าวสวยหรือขนมจีน เพิ่มรสชาติให้อาหารมื้อนั้นพิเศษยิ่งขึ้น.",
      "doc": "food" },
    { "text": "ส้มตำไทยเป็นสลัดมะละกอดิบที่มีรสเปรี้ยว หวาน เค็ม และเผ็ดผสมผสานกันอย่างลงตัว มักใส่ถั่วลิสง กุ้งแห้ง และมะเขือเทศ ทานคู่กับข้าวเหนียวและไก่ย่าง เป็นเมนูยอดฮิตของภาคอีสานที่คนทั่วประเทศชื่นชอบ.",
      "doc": "food" }
]

bulk_docs = []

for i, item in enumerate(texts):
    
    text = item['text']
    doc = item['doc']

    vec = get_embedding(text).tolist()
    
    action = {
        "_index": INDEX_NAME,
        "_id": f"doc_{doc}_{i+1}",
        "_source": {
            "text": text,
            "doc": doc,  # เปลี่ยนจาก filename เป็น doc
            "embedding": vec
        }
    }
    bulk_docs.append(action)

success, failed = helpers.bulk(client, bulk_docs, stats_only=True)
print(f"Bulk indexing complete: {success} succeeded, {failed} failed.")


######## Query ##############


query = "มีข้าวมันไก่เป็นอาหารจานเดียวที่ได้รับความนิยมอย่างแพร่หลาย"
query_vector = get_embedding(query).tolist()

query_body = {
    "size": 5,
    "query": {
        "knn": {
            "embedding": {
                "vector": query_vector,
                "k": 5  # คืนผลลัพธ์ 5 อันดับแรก
            }
        }
    }
}

response = client.search(index=INDEX_NAME, body=query_body)
for hit in response['hits']['hits']:
    print(f"Score: {hit['_score']:.4f}, Text: {hit['_source']['text']}")
    
    

