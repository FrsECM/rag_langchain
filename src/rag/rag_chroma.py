from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores.chroma import Chroma
from langchain.docstore.document import Document
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from typing import List
from tqdm.auto import tqdm
import openai
import json
import os

class CHROMA_RAG():
    def __init__(self,db_dir:str) -> None:
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        # Splitter 
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1000,
            chunk_overlap  = 20,
            length_function = len,
            add_start_index=True)
        # We create a text embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cuda'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.db_dir = db_dir
        self.config_path = os.path.join(self.db_dir,'config.json')
        # Chroma
        self.db = Chroma(collection_name='chroma_db',embedding_function=self.embeddings,persist_directory=db_dir)

        self.law_texts=None
        self.load_config()
    
    def save_config(self):
        with open(self.config_path,'w',encoding='utf8') as jsf:
            json.dump({'law_texts':self.law_texts},jsf,default='str',ensure_ascii=False,indent=4)

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path,'r') as jsf:
                config = json.load(jsf)
                self.law_texts = config['law_texts']
        else:
            self.law_texts = []
            self.save_config()

    def create_db(self,db_path:str):
        self.db = Chroma(collection_name='chroma_db',embedding_function=self.embeddings,persist_directory=db_path)
    
    def create_documents(self,texts:List[str],metadatas:List[dict]):
        assert len(texts)==len(metadatas),f'Lenght of texts and metadata should be equals {len(texts)} / {len(metadatas)} given'
        documents=[]
        for text,metadata in tqdm(zip(texts,metadatas),total=len(texts)):
            chunks = self.text_splitter.split_text(text)
            docs = [Document(page_content=c,metadata=metadata) for c in chunks]
            documents.extend(docs)
        return documents


    def add_documents(self,documents:List[Document],law_text_title:str):
        if len(documents)>0:
            self.law_texts.append(law_text_title)
            self.db.add_documents(documents)
            self.save_config()

    def retrieve(self,query,k=10):
        embedding_vector = self.embeddings.embed_query(query)
        docs_and_scores = self.db.similarity_search_by_vector_with_relevance_scores(embedding_vector,k=k)
        return docs_and_scores

    def generate(self,query,k=10):
        self.template = """You are a lawyer who advise genuine people's questions.
        Answer the question based only on the following context ; 
        {context}
        You must respect theses rules : 
        -   The answer should be in the same language than the question.
        -   Use bulletpoints when multiple answers
        -   Add a Sources section in the end that reference documents from the context that are used in the answer and only them.

        Question: {question}
        """

        prompt = ChatPromptTemplate.from_template(self.template)

        assert self.db is not None,"Load or Create a database before generating..."
        def format_docs(docs):
            result = ""
            for doc in docs:
                result+=f"\n\n{doc.metadata['content']}\nSource:\n{doc.metadata['source']}"
            return result
        retriever = self.db.as_retriever(search_kwargs={'k':k})
        model = AzureChatOpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            azure_endpoint =os.getenv('OPENAI_BASE_URL'),
            model=os.getenv('OPENAI_MODEL'),
            api_version="2023-07-01-preview")
        
        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | model
            | StrOutputParser()
        )
        return chain.invoke(query)

