# uncompyle6 version 3.9.0
# Python bytecode version base 3.8.0 (3413)
# Decompiled from: Python 3.8.18 | packaged by conda-forge | (default, Oct 10 2023, 15:44:36) 
# [GCC 12.3.0]
# Embedded file name: /mnt/c/BUSCODE/perso/langchain_law/notebooks/../src/legifrance/legifrance_orm.py
# Compiled at: 2023-11-13 22:13:15
# Size of source mod 2**32: 5723 bytes
from typing import List, Optional
from sqlalchemy import String, DateTime, Integer, ForeignKey, Boolean
import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime

class Base(DeclarativeBase):
    pass


class LawText(Base):
    __tablename__ = 'LEGI_TEXT'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=(lambda: str(uuid.uuid4())))
    legi_id: Mapped[str] = mapped_column(String,unique=True)
    active: Mapped[Optional[bool]] = mapped_column(Boolean)
    title: Mapped[Optional[str]] = mapped_column(String)
    
    created_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    modif_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    
    sections: Mapped[Optional[List['Section']]] = relationship(back_populates='lawtext')
    
    def __repr__(self) -> str:
        return f"LawText(id={self.id!r}, title={self.title})"

    def from_json(result: dict):
        date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
        return LawText(
            legi_id=result['id'],
            active=result['etat'] == 'VIGUEUR',
            title=result['titre'],
            created_date=datetime.strptime(result['dateDebut'],date_format),
            modif_date=datetime.strptime(result['lastUpdate'],date_format)
        )


class Section(Base):
    __tablename__ = 'LEGI_SECTION'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=(lambda: str(uuid.uuid4())))
    legi_id: Mapped[str] = mapped_column(String,unique=True)
    active: Mapped[Optional[bool]] = mapped_column(Boolean)
    title: Mapped[str] = mapped_column(String)
    
    intOrdre: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    modif_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.fromisoformat('1804-03-21')))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    
    lawtext_id: Mapped[str] = mapped_column(String, ForeignKey('LEGI_TEXT.id'))
    lawtext: Mapped['LawText'] = relationship(back_populates='sections')
    
    section_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('LEGI_SECTION.id'))    
    section: Mapped[Optional['Section']] = relationship(remote_side=[id])

    articles: Mapped[Optional[List['Article']]] = relationship(back_populates='section')
    

    def __repr__(self) -> str:
        return f"Section(id={self.id!r}, title={self.title})"


class Article(Base):
    __tablename__ = 'LEGI_ART'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=(lambda: str(uuid.uuid4())))
    legi_id: Mapped[str] = mapped_column(String,unique=True)
    active: Mapped[Optional[bool]] = mapped_column(Boolean)
    title: Mapped[str] = mapped_column(String)
    
    num: Mapped[str] = mapped_column(String(30))
    
    section_id: Mapped[str] = mapped_column(String, ForeignKey('LEGI_SECTION.id'))
    section: Mapped['Section'] = relationship(back_populates='articles')
    
    content: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    nota: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    created_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    modif_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.utcnow))
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=(datetime.fromisoformat('1804-03-21')))
    
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)
    

    def __repr__(self) -> str:
        return f"Article(cid={self.id!r}, title={self.title})"


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
        section3.section = section2
        session.add_all([section1, section2, section3])
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