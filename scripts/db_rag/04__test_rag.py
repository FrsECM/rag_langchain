import sys
import os
os.environ['TOKENIZERS_PARALLELISM']='false'

from src.rag import CHROMA_RAG, add_backline

pipeline = CHROMA_RAG('../data/chroma')
question = "Quelles sont les conditions du droit de préemption ?"
res_rag = pipeline.generate(question,5)
print(add_backline(res_rag))