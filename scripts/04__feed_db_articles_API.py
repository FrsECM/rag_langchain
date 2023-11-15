from src.legifrance import LegifranceClient,LegifranceDatabase

from src.legifrance.orm import Article,Section,LawText
from sqlalchemy import select,and_,Row
import argparse
from tqdm.auto import tqdm
from typing import Tuple,Dict
from concurrent.futures import ThreadPoolExecutor,as_completed
import os

parser = argparse.ArgumentParser()
parser.add_argument('--db_path',default='data/sqlite/legifrance.db')
parser.add_argument('--text_name',default='Code du Tourisme')
parser.add_argument('--update_articles',action='store_true',default=True)


def main(db_path:str,text_name:str,update_articles:bool):
    database = LegifranceDatabase(path=db_path)
    client = LegifranceClient(api_limit_per_second=1)
    law_text_query = select(LawText).where(LawText.title.contains(text_name))
    db_lawtexts = [d[0] for d in database.session.execute(law_text_query).all() if isinstance(d,Row)]
    # We only update newly created...
    if update_articles:
        for text in db_lawtexts:
            text:LawText
            # We indexed by article then it will be fast...
            articles = text.get_all_articles()
            p_bar = tqdm(desc=text.title,total=len(articles))
            def get_article_dict(article_legi_id,i):
                return i,client.get_article_dict(article_legi_id)
            futures=[]
            # max_workers = 1 => No parallel..
            with ThreadPoolExecutor(max_workers=1) as executor:
                for i,article in enumerate(articles):
                        futures.append(executor.submit(get_article_dict,article.legi_id,i))
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
                        p_bar.set_postfix(**{'article':f"Art. {article.num}"})
                    else:
                        article.empty = True
                    p_bar.update(1)
                    database.commit()



if __name__=='__main__':
    args = parser.parse_args()
    main(**vars(args))