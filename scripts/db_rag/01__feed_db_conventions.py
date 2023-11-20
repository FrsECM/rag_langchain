from src.legifrance import LegifranceClient,LegifranceDatabase,LegifranceScrapper
from src.legifrance.orm import Article,Section,LawText,CollectiveConvention
from sqlalchemy import select,and_
import argparse
from tqdm.auto import tqdm
from typing import Tuple,Dict
from concurrent.futures import ThreadPoolExecutor,as_completed
import os

parser = argparse.ArgumentParser()
parser.add_argument('--db_path',default='data/sqlite/legifrance.db')
parser.add_argument('--db_reset',action='store_true',default=False)
parser.add_argument('--convention_name',default='caoutchouc')


def main(db_path:str,db_reset:bool,convention_name:str):
    database = LegifranceDatabase(path=db_path)
    database.create_database(overwrite=db_reset,exist_ok=True)
    scrapper = LegifranceScrapper()
    client = LegifranceClient(production=False)

    convention_list = scrapper.list_conventions(convention_name)
    db_conventions = database.session.query(CollectiveConvention).where(CollectiveConvention.legi_id.in_([c['legi_id'] for c in convention_list])).all()
    existing_conventions = {c.legi_id:c for c in db_conventions}
    convention_to_add = [c for c in convention_list if c['legi_id'] not in existing_conventions]

    created_conventions = []
    for i,convention_dict in enumerate(convention_to_add):
        convention = CollectiveConvention(
            legi_id = convention_dict['legi_id'],
            active=True,
            title=convention_dict['title']
        )
        created_conventions.append(convention)

    for convention in created_conventions:
        convention:CollectiveConvention
        if len(convention.sections)==0:
            convention = client.get_convention(convention)
            articles = convention.get_all_articles()
            for article in tqdm(articles.values(),desc=convention.title):
                article.title = f"{convention.title} - Art. {article.num}"
                article.content = article.content.strip()
                article.active = True
    database.session.add_all(created_conventions)
    database.commit()




if __name__=='__main__':
    args = parser.parse_args()
    main(**vars(args))