# uncompyle6 version 3.9.0
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.18 | packaged by conda-forge | (default, Oct 10 2023, 15:44:36) 
# [GCC 12.3.0]
# Embedded file name: /mnt/c/BUSCODE/perso/langchain_law/notebooks/../src/legifrance/legifrance_orm.py
# Compiled at: 2023-11-13 22:13:15
# Size of source mod 2**32: 5723 bytes
from typing import List, Optional,Dict
from sqlalchemy import String, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy import select
import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from .utils import parse_date
from sqlalchemy.engine import Engine
from sqlalchemy import event
import re


def is_active(etat:str):
    return 'VIGUEUR' in etat

class Base(DeclarativeBase):
    pass


class LawText(Base):
    __tablename__ = 'LEGI_TEXT'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    legi_id: Mapped[str] = mapped_column(String)
    active: Mapped[Optional[bool]] = mapped_column(Boolean)
    title: Mapped[Optional[str]] = mapped_column(String)
    
    created_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    modif_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    
    sections: Mapped[List['Section']] = relationship(back_populates='lawtext',cascade='save-update, merge, delete, delete-orphan',passive_deletes=True)
    
    def get_all_sections(self)->Dict[str,'Section']:
        sections = {s.legi_id:s for s in self.sections}
        # We add articles...
        # We add subsections articles...
        for section in self.sections:
            sections.update(section.get_sections())
        return sections

    def get_all_articles(self)->Dict[str,'Article']:
        articles = {}
        # We add articles...
        # We add subsections articles...
        for section in self.sections:
            articles.update(section.get_articles())
        return articles

    def __eq__(self, other: 'LawText') -> bool:
        return self.legi_id == other.legi_id

    def __repr__(self) -> str:
        return f"LawText(legi_id={self.legi_id!r}, title={self.title})"

    def from_json(result: dict):
        date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
        return LawText(
            legi_id=result['id'],
            active=is_active(result['etat']),
            title=result['titre'],
            created_date=datetime.strptime(result['dateDebut'],date_format),
            modif_date=datetime.strptime(result['lastUpdate'],date_format)
        )

class CollectiveConvention(Base):
    __tablename__ = 'LEGI_CONV'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    legi_id: Mapped[str] = mapped_column(String)
    active: Mapped[Optional[bool]] = mapped_column(Boolean)
    title: Mapped[Optional[str]] = mapped_column(String)
    
    created_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    modif_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    
    sections: Mapped[List['Section']] = relationship(back_populates='convention',cascade='save-update, merge, delete, delete-orphan',passive_deletes=True)
    articles:Mapped[List['Article']] = relationship(back_populates='convention',cascade='save-update, merge, delete, delete-orphan',passive_deletes=True)

    def get_all_sections(self)->Dict[str,'Section']:
        sections = {s.legi_id:s for s in self.sections}
        # We add articles...
        # We add subsections articles...
        for section in self.sections:
            sections.update(section.get_sections())
        return sections

    def get_all_articles(self)->Dict[str,'Article']:
        articles = {a.legi_id:a for a in self.articles}
        # We add articles...
        # We add subsections articles...
        for section in self.sections:
            articles.update(section.get_articles())
        return articles

    def __eq__(self, other: 'LawText') -> bool:
        return self.legi_id == other.legi_id

    def __repr__(self) -> str:
        return f"CollectiveConvention(legi_id={self.legi_id!r}, title={self.title})"

    def from_json(result: dict):
        date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
        return LawText(
            legi_id=result['id'],
            active=is_active(result['etat']),
            title=result['titre'],
            created_date=datetime.strptime(result['dateDebut'],date_format),
            modif_date=datetime.strptime(result['lastUpdate'],date_format)
        )

class Section(Base):
    __tablename__ = 'LEGI_SECTION'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True,index=True)
    legi_id: Mapped[str] = mapped_column(String)
    active: Mapped[Optional[bool]] = mapped_column(Boolean)
    title: Mapped[str] = mapped_column(String)
    
    intOrdre: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    modif_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.fromisoformat('1804-03-21')))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    # Possible Parents
    lawtext_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('LEGI_TEXT.id',ondelete='CASCADE'),index=True)
    lawtext: Mapped[Optional['LawText']] = relationship(back_populates='sections')

    convention_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('LEGI_CONV.id',ondelete='CASCADE'),index=True)    
    convention: Mapped[Optional['CollectiveConvention']] = relationship(back_populates='sections')

    section_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('LEGI_SECTION.id',ondelete='CASCADE'),index=True)    
    section: Mapped[Optional['Section']] = relationship(remote_side=[id])
    # Possible Childs
    sections: Mapped[List['Section']] = relationship(back_populates='section',cascade='save-update, merge, delete, delete-orphan',passive_deletes=True)
    articles: Mapped[List['Article']] = relationship(back_populates='section',cascade='save-update, merge, delete, delete-orphan',passive_deletes=True)
    
    def get_articles(self)->Dict[str,'Article']:
        articles = {a.legi_id:a for a in self.articles}
        # We add articles...
        # We add subsections articles...
        for section in self.sections:
            articles.update(section.get_articles())
        return articles

    def get_sections(self)->Dict[str,'Section']:
        sections={s.legi_id:s for s in self.sections}
        for section in self.sections:
            sections.update(section.get_sections())
        return sections

    def __repr__(self) -> str:
        return f"Section(legi_id={self.legi_id!r}, title={self.title})"

    def __eq__(self, other: 'Section') -> bool:
        return self.legi_id == other.legi_id

    def from_json(result: dict):
        sections = [Section.from_json(s) for s in result['sections']]
        articles = [Article.from_json(s) for s in result['articles']]
        section = Section(
            legi_id=result['id'],
            active=is_active(result['etat']),
            title=result['title'],
            intOrdre=result['intOrdre'],
            start_date = parse_date(result['dateDebut']),
            end_date = parse_date(result['dateFin']),
            created_date=parse_date(result['dateDebut']),
            modif_date=parse_date(result['dateModif']) if result['dateModif'] else datetime.now()
        )
        section.sections = sections
        section.articles = articles
        return section

class Article(Base):
    __tablename__ = 'LEGI_ART'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True,index=True)
    legi_id: Mapped[str] = mapped_column(String)
    active: Mapped[Optional[bool]] = mapped_column(Boolean)
    empty: Mapped[Optional[bool]] = mapped_column(Boolean,default=False)
    num: Mapped[str] = mapped_column(String(30))

    # Possible Parents
    section_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('LEGI_SECTION.id',ondelete='CASCADE'),index=True)
    section: Mapped[Optional['Section']] = relationship(back_populates='articles')

    convention_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('LEGI_CONV.id',ondelete='CASCADE'),index=True)    
    convention: Mapped[Optional['CollectiveConvention']] = relationship(back_populates='articles')

    version: Mapped[Optional[str]] = mapped_column(String(30))
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    nota: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    created_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    modif_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.fromisoformat('1804-03-21')))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)    

    def __repr__(self) -> str:
        return f"Article(legi_id={self.legi_id!r}, title={self.title})"
    
    def from_json(result: dict):
        article = Article(
            legi_id=result['id'],
            active=is_active(result['etat']),
            num=f"{result['num']}",
        )
        def feed(article:Article,source:dict,prop_name:str):
            if prop_name in source:
                value = source[prop_name]
                if isinstance(value,str):
                    value=re.sub(r'<.*?>','',value)
                setattr(article,prop_name,value)        
        for prop in ['content','nota']:
            feed(article,result,prop)
        return article

    def update(self,result:dict):
        self.version = result['versionArticle']
        self.start_date = datetime.fromtimestamp(result['dateDebut']/1e3)
        self.end_date = datetime.fromtimestamp(result['dateFin']/1e3)
        self.content = result['texte']
        self.nota = result['nota']


if __name__ == '__main__':
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from sqlalchemy import select, func
    import os
    if os.path.exists('data/legifrance/database.db'):
        os.remove('data/legifrance/database.db')
    engine = create_engine('sqlite:///data/legifrance/database.db', echo=True)
    Base.metadata.create_all(engine)
    with Session(engine) as (session):
        law_text = LawText(legi_id='LEGITEXT0000', active=True,
          title='Texte Bullshit')
        session.add(law_text)
        session.commit()
    with Session(engine) as (session):
        texte_query = select(LawText).where(LawText.legi_id == 'LEGITEXT0000')
        result = session.execute(texte_query)
        law_text = next(result)[0]
        section1 = Section(legi_id='LEGISECT0000', active=True,
          title='My Section')
        section1.lawtext = law_text
        section2 = Section(legi_id='LEGISECT0001', active=True,
          title='My Section2')
        section2.lawtext = law_text
        section3 = Section(legi_id='LEGISECT0002', active=True,
          title='My sous section1')
        section3.lawtext = law_text
        section2.sections.append(section3)
        session.add_all([section1, section2])
        session.commit()
    with Session(engine) as (session):
        section_query = select(Section)
        result = session.execute(section_query)
        count = session.query(func.count(Section.legi_id)).scalar()
        section = next(result)[0]
        article = Article(legi_id='LEGIART0001',
          active=True,
          title='Mon Article',
          num='2-10')
        article.section = section
        session.add(article)
        session.commit()