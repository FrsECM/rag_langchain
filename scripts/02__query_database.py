import argparse
import re
from src.rag import RAG_Pipeline
import os

parser = argparse.ArgumentParser()
parser.add_argument('--query',default="Qu'est ce qu'une servitude ?")
parser.add_argument('--db',default="faiss_db")

def query_database(query:str,db:str):
    pipeline = RAG_Pipeline()
    pipeline.load('faiss_db')
    response = pipeline.generate(query,k=20)
    return response



if __name__=='__main__':
    args = parser.parse_args()
    query_database(**vars(args))
    