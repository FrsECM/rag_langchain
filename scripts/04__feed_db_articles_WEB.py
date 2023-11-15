from src.legifrance import LegifranceClient,LegifranceDatabase
from src.legifrance.legifrance_scrapper import LegifranceScrapper

from src.legifrance.orm import Article,Section,LawText
from sqlalchemy import select,and_,Row
import argparse
from tqdm.auto import tqdm
from typing import Tuple,Dict
from concurrent.futures import ThreadPoolExecutor,as_completed
import os

parser = argparse.ArgumentParser()
parser.add_argument('--db_path',default='data/sqlite/legifrance.db')
parser.add_argument('--text_name',default="Code de l'urbanisme")
parser.add_argument('--update_articles',action='store_true',default=True)


def main(db_path:str,text_name:str,update_articles:bool):
    database = LegifranceDatabase(path=db_path)
    scrapper = LegifranceScrapper()
    law_text_query = select(LawText).where(LawText.title.contains(text_name))
    db_lawtexts = [d[0] for d in database.session.execute(law_text_query).all() if isinstance(d,Row)]
    # We only update newly created...
    if update_articles:
        for text in db_lawtexts:
            # We indexed by article then it will be fast...
            sections = text.get_all_sections()
            p_bar = tqdm(sections,desc=text.title)
            for section in p_bar:
                article_list=scrapper.get_section(section_legi_id=section.legi_id,text_legi_id=text.legi_id)
                for i,article_dict in enumerate(article_list):
                    select_instance = select(Article).where(
                        and_(
                            Article.section_id==section.id,
                            Article.legi_id==article_dict['legi_id']
                        )
                    )
                    result = database.session.execute(select_instance).first()
                    postfix = {'article':f"{i+1}/{len(article_list)}",'title':'None'}
                    if result is not None:
                        article = result[0]
                        article:Article
                        title = article_dict['title']
                        parent_lawtext = None
                        parent = article
                        while parent_lawtext is None:
                            parent = parent.section
                            parent_lawtext = parent.lawtext
                            root = parent.title.split(':')[0].strip()
                            title=f"{root} - {title}"
                        title = f"{text.title} - {title}"
                        article.title = title
                        article.empty = False
                        article.active = not article_dict['is_abrogated']
                        article.content = article_dict['content']
                        postfix.update({'title':article_dict['title']})
                        database.commit()
                    p_bar.set_postfix(**postfix)



if __name__=='__main__':
    args = parser.parse_args()
    main(**vars(args))