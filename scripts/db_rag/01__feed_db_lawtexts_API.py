from src.legifrance import LegifranceClient,LegifranceDatabase
from src.legifrance.orm import Article,Section,LawText
from sqlalchemy import select,and_
import argparse
from tqdm.auto import tqdm
from typing import Tuple,Dict
from concurrent.futures import ThreadPoolExecutor,as_completed
import os

parser = argparse.ArgumentParser()
parser.add_argument('--db_path',default='data/sqlite/legifrance.db')
parser.add_argument('--db_reset',action='store_true',default=False)
parser.add_argument('--law_text',default='impôt')
parser.add_argument('--update_articles',action='store_true',default=True)


def main(db_path:str,db_reset:bool,law_text:str,update_articles:bool):
    database = LegifranceDatabase(path=db_path)
    database.create_database(overwrite=db_reset,exist_ok=True)

    client = LegifranceClient(production=False)
    api_lawtexts = []
    if law_text:
        api_lawtexts = client.list_lawtexts(law_text)
        existing_law_texts = database.get_all_lawtexts()
        law_texts_to_add =[t for t in api_lawtexts if t not in existing_law_texts]
        database.add_lawtexts(law_texts_to_add)
        # We only update newly created...
        for i,text in enumerate(law_texts_to_add):
            print(f'{text.title} - {i+1}/{len(law_text)}')
            sections = client.get_lawtext(text)
            database.add_sections(lawtext=text,sections=sections)
            database.commit()




if __name__=='__main__':
    args = parser.parse_args()
    main(**vars(args))