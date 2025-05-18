# -*- coding: utf-8 -*-
import numpy as np


from opensearchpy import OpenSearch, helpers
#from langchain_community.vectorstores import OpenSearchVectorSearch

from transformers import AutoTokenizer, AutoModel
import torch

#import deepcut

class EmbeddingModel:
    
    BGE_M3 = 'BAAI/bge-m3'
    BGE_RERANKER_V2_M3 = 'BAAI/bge-reranker-v2-m3'
    
    def __init__(self, em_name):
        self.em_name = em_name
        self.tokenizer = AutoTokenizer.from_pretrained(em_name)
        self.model = AutoModel.from_pretrained(em_name)
        


class RAG_OpenSearch:
    
    
    def __init__(self):
        pass
        
    def connect_vector_db(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        self.client = OpenSearch(
                        hosts=[ {'host': self.host, 'port': self.port}],
                        http_compress=True,
                        http_auth=(self.username, self.password),
                        use_ssl=False
                    )
        
        
    def set_embedding_model(self, embedding):
        self.k_em = embedding
        self.q_em = embedding
        
    def set_embedding_models(self, key_embedding, query_embedding):
        self.k_em = key_embedding
        self.q_em = query_embedding
        
    
    def get_embedding(self, embedding, text):
        inputs = embedding.tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
        with torch.no_grad():
            outputs = embedding.model(**inputs)
        em_vector = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
        return em_vector / np.linalg.norm(em_vector) 
    
    def get_k_embedding(self, text):
        return self.get_embedding(self.k_em, text)
    
    def get_q_embedding(self, text):
        return self.get_embedding(self.q_em, text)
    
    def create_vector_space(self, space_name):
        
        if not self.client.indices.exists(index=space_name):
    
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
                                "engine": "faiss",
                                "space_type": "cosinesimil"
                            }
                        }
                    }
                }
            }
    
            
            self.client.indices.create(space_name, body=index_body)
            print(f"Index '{space_name}' created.")
        else:
            print(f"Index '{space_name}' already exists.")
            
    def delete_vector_space(self, space_name):
        if self.client.indices.exists(index=space_name):
            self.client.indices.delete( index = space_name )
            
    
    def store_one_item(self, space_name, item):
        item["embedding"] = self.get_k_embedding(item['text']).tolist()
        response = self.client.index(index=space_name, body=item)
        print(f"Document indexed with ID: {response['_id']}")
        
    def store_many_items(self, space_name, items):
        bulk_docs = []

        for i, item in enumerate(items):
            
            text = item['text']
            doc = item['doc']

            vec = self.get_k_embedding(text).tolist()
            
            action = {
                "_index": space_name,
                "_id": f"doc_{doc}_{i+1}",
                "_source": {
                    "text": text,
                    "doc": doc,  # เปลี่ยนจาก filename เป็น doc
                    "embedding": vec
                }
            }
            
            bulk_docs.append(action)

        success, failed = helpers.bulk(self.client, bulk_docs, stats_only=True)
        print(f"Bulk indexing complete: {success} succeeded, {failed} failed.")
        
        
    def query(self, space_name, query, top_k=5):
        query_vector = self.get_q_embedding(query).tolist()

        query_body = {
            "size": 5,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": top_k
                    }
                }
            }
        }

        response = self.client.search(index=space_name, body=query_body)
        
        res_list = []
        for hit in response['hits']['hits']:
            
            res = (hit['_source']['text'], round(hit['_score'], 4))
            res_list.append(res)
            #print(f"Score: {hit['_score']:.4f}, Text: {hit['_source']['text']}")

        return res_list





    

