from src.legifrance import LegifranceClient,LegifranceDatabase
from src.legifrance.orm import Article,Section,LawText
from sqlalchemy import select,and_
import argparse
from tqdm.auto import tqdm
from typing import Tuple,Dict
from concurrent.futures import ThreadPoolExecutor,as_completed
import os

parser = argparse.ArgumentParser()
parser.add_argument('--db_path',default='data/legifrance/database.db')
parser.add_argument('--db_reset',action='store_true',default=False)
parser.add_argument('--law_text',default=None)
parser.add_argument('--update_articles',action='store_true',default=True)


def main(db_path:str,db_reset:bool,law_text:str,update_articles:bool):
    database = LegifranceDatabase(path=db_path)
    database.create_database(overwrite=db_reset,exist_ok=True)

    client = LegifranceClient(production=False)
    api_lawtexts = []
    if law_text:
        api_lawtexts = client.list_lawtexts(law_text)
        existing_law_texts = database.get_all_lawtexts()
        database.add_lawtexts([t for t in api_lawtexts if t not in existing_law_texts])
    # We get all_lawtexts...
    db_lawtexts = database.get_all_lawtexts()
    # We only update newly created...
    for text in [t for t in db_lawtexts if t in api_lawtexts]:
        sections = client.get_lawtext(text)
        database.add_sections(lawtext=text,sections=sections)
        database.commit()
    if update_articles:
        for text in db_lawtexts:
            # We indexed by article then it will be fast...
            articles = text.get_all_articles()
            p_bar = tqdm(desc=text.title,total=len(articles))
            def get_article_dict(article_legi_id,i):
                return i,client.get_article_dict(article_legi_id)
            futures=[]
            # max_workers = 1 => No parallel..
            with ThreadPoolExecutor(max_workers=1) as executor:
                for i,article in enumerate(articles):
                    if article.content is None:
                        futures.append(executor.submit(get_article_dict,article.legi_id,i))
                    else:
                        p_bar.set_postfix(**{'article':article.title})
                        p_bar.update(1)
                for future in as_completed(futures):
                    i,a_dict = future.result()
                    article = articles[i]
                    article:Article
                    if a_dict is not None:
                        title = f"Art. {article.num}"
                        parent_lawtext = None
                        parent = article
                        while parent_lawtext is None:
                            parent = parent.section
                            parent_lawtext = parent.lawtext
                            root = parent.title.split(':')[0].strip()
                            title=f"{root} - {title}"
                        title = f"{text.title} - {title}"
                        article.title = title
                        article.update(a_dict)
                        article.empty = False
                        p_bar.set_postfix(**{'article':article.title})
                    else:
                        article.empty = True
                    p_bar.update(1)
            database.commit()



if __name__=='__main__':
    args = parser.parse_args()
    main(**vars(args))