from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import select,func
from typing import Union,List
from .orm import Base,LawText,Section,Article
import os

class LegifranceDatabase:
    def __init__(self,path:str):
        self.path = path
        self.engine = create_engine(f'sqlite:///{path}',echo=True)

    def create_database(self,overwrite:bool=False):
        """Create the database if it doesn't exists

        Args:
            overwrite (bool, optional): _description_. Defaults to True.

        Raises:
            Exception: _description_
        """
        if os.path.exists(self.path):
            if overwrite:
                os.remove(self.path)
            else:
                raise Exception(f'Database {self.path} already exists...')
        Base.metadata.create_all(self.engine)
    
    def add_text(self,text:LawText):
        assert isinstance(text,LawText),"text should be a LawText object"
        with Session(self.engine) as session:
            session.add(text)
            session.commit()
    
    def add_texts(self,texts:List[LawText]):
        assert isinstance(texts,list),"texts should be a list of LawText"
        with Session(self.engine) as session:
            session.add_all(texts)
            session.commit()    