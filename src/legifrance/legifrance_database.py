from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select,func,or_,and_
from typing import Union,List
from .orm import Base,LawText,Section,Article,CollectiveConvention
import os

from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class LegifranceDatabase:
    def __init__(self,path:str,sync:bool=True):
        self.path = path
        if sync:
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

    def get_lawtexts(self,title_str:str)->List[LawText]:
        """Get lawtexts that correspond to an input string.

        Args:
            title_str (str): _description_

        Returns:
            List[LawText]: _description_
        """
        query = select(LawText).where(
            or_(
                LawText.title.like(title_str),
                LawText.title.contains(title_str),
                LawText.legi_id.like(title_str)
                )
        )
        results = self.session.execute(query).all()
        return [r[0] for r in results]

    def get_conventions(self,title_str:str)->List[CollectiveConvention]:
        """Get conventions that correspond to an input string.

        Args:
            title_str (str): _description_

        Returns:
            List[CollectiveConvention]: _description_
        """
        query = select(CollectiveConvention).where(
            and_(
                CollectiveConvention.title.startswith('Convention'),
                or_(
                    CollectiveConvention.title.like(title_str),
                    CollectiveConvention.title.contains(title_str)
                )
                )
        )
        results = self.session.execute(query).all()
        return [r[0] for r in results]


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
