from src.legifrance import LegifranceClient,LegifranceDatabase
from src.legifrance.orm import Article
import argparse
from tqdm.auto import tqdm
from typing import Tuple,Dict

parser = argparse.ArgumentParser()
parser.add_argument('--db_path',default='data/legifrance/database.db')
parser.add_argument('--db_reset',action='store_true',default=True)
parser.add_argument('--law_text',default='code')
parser.add_argument('--update_articles',action='store_true',default=True)


def main(db_path:str,db_reset:bool,law_text:str,update_articles:bool):
    database = LegifranceDatabase(path=db_path)
    database.create_database(overwrite=db_reset,exist_ok=True)

    client = LegifranceClient()
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
            articles = [a for a in text.get_articles() if not a.empty and a.content is None]
            # It's slow, then we'll accelerate it with concurent querying.
            def get_article_dict(article:Article)->Tuple[Article,Dict]:
                return article,client.get_article_dict(article)
            a_bar = tqdm(articles,desc=text.title)
            for article in a_bar:
                _,dict = get_article_dict(article)
                article:Article
                dict:dict
                if dict is not None:
                    article.title = f"{text.title} - {article.section.title} - Art. {article.num}"
                    article.update(dict)
                    article.empty=False
                else:
                    article.empty=True
                database.commit()
                a_bar.set_postfix(**{'article':f'Art. {article.num}'})



if __name__=='__main__':
    args = parser.parse_args()
    main(**vars(args))