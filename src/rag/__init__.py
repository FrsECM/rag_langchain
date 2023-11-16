from .rag_faiss import FAISS_RAG
from .rag_chroma import CHROMA_RAG

def add_backline(text,frequency=15):
    res = ""
    index = 0
    for char in str(text):
        if char =='\n':
            index=0
        if char == ' ':
            index+=1
            if not index%frequency:
                res+='\n'
                continue
        res+=char
    return res