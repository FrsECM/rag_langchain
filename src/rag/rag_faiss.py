from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores.faiss import FAISS
from langchain.document_loaders import TextLoader
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

import openai
import os

class FAISS_RAG():
    def __init__(self) -> None:
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
        self.db = None
        template = """Answer the question based only on the following context

        {context}

        You must respect theses rules : 
        -   The answer should be in the same language than the question.
        -   Use bulletpoints when multiple answers
        -   Add a Sources section in the end that reference document and position of the informations provided
        Question: {question}
        """
        self.prompt = ChatPromptTemplate.from_template(template)

    def create_db(self,src_text_dir):
        txt_filepaths= [os.path.join(src_text_dir,f) for f in os.listdir(src_text_dir)]
        docs = []
        for file_path in txt_filepaths:
            document = TextLoader(file_path).load()
            docs.extend(self.text_splitter.split_documents(document))

        self.db = FAISS.from_documents(docs, self.embeddings)
    
    def save(self,path:str="faiss_db"):
        self.db.save_local(path)

    def load(self,path:str="faiss_db"):    
        self.db=FAISS.load_local(path,self.embeddings)

    def retrieve(self,query,k=10):
        embedding_vector = self.embeddings.embed_query(query)
        docs_and_scores = self.db.similarity_search_by_vector(embedding_vector,k=k)
        return docs_and_scores

    def generate(self,query,k=10):
        assert self.db is not None,"Load or Create a database before generating..."
        def format_docs(docs):
            result = ""
            for doc in docs:
                result+=f"\n\n{doc.page_content}\nSources:\- {doc.metadata['title']}"
            return result
        retriever = self.db.as_retriever(search_kwargs={'k':k})
        model = AzureChatOpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            azure_endpoint =os.getenv('OPENAI_BASE_URL'),
            model=os.getenv('OPENAI_MODEL'),
            api_version="2023-07-01-preview")
        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | model
            | StrOutputParser()
        )
        return chain.invoke(query)

