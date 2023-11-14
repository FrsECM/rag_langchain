from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select,func
from typing import Union,List
from .orm import Base,LawText,Section,Article
import os

from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class LegifranceDatabase:
    def __init__(self,path:str):
        self.path = path
        self.engine = create_engine(f'sqlite:///{path}',echo=False)
        self.session = sessionmaker(bind=self.engine)()

    def __del__(self):
        self.session.close()

    def create_database(self,overwrite:bool=False,exist_ok:bool=False):
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
                if not exist_ok:
                    raise Exception(f'Database {self.path} already exists...')
                else:
                    return
        Base.metadata.create_all(self.engine)
    
    def add_lawtext(self,lawtext:LawText):
        assert isinstance(lawtext,LawText),"text should be a LawText object"
        self.session.add(lawtext)
        self.session.commit()
    
    def add_lawtexts(self,lawtexts:List[LawText]):
        assert isinstance(lawtexts,list),"texts should be a list of LawText"
        self.session.add_all(lawtexts)
        self.session.commit()

    def get_all_lawtexts(self):
        result = self.session.query(LawText).all()
        return result

    def get_all_articles(self):
        result = self.session.query(Article).all()
        return result
    
    def add_sections(self,lawtext:LawText,sections:List[Section]):
        for section in sections:
            if section not in lawtext.sections:
                lawtext.sections.append(section)

    def commit(self):
        self.session.commit()
