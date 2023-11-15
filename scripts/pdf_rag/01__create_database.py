import argparse
import re
from src.rag import FAISS_RAG
import os

parser = argparse.ArgumentParser()
parser.add_argument('--txt_dir',default="data/txt")


def create_database(txt_dir:str):
    pipeline = FAISS_RAG()
    pipeline.create_db(txt_dir)
    pipeline.save('faiss_db')




if __name__=='__main__':
    args = parser.parse_args()
    create_database(**vars(args))
    