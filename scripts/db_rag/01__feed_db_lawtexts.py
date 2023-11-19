from src.legifrance import LegifranceClient,LegifranceDatabase,LegifranceScrapper
from src.legifrance.orm import Article,Section,LawText
from sqlalchemy import select,and_,func
import argparse
from tqdm.auto import tqdm


parser = argparse.ArgumentParser()
parser.add_argument('--db_path',default='data/sqlite/legifrance.db')
parser.add_argument('--db_reset',action='store_true',default=False)
#parser.add_argument('--law_names',default='urbanisme|impôt|rural|Code civil|forestier|commune|tourisme')
parser.add_argument('--law_names',default='travail')


def main(db_path:str,db_reset:bool,law_names:str):
    database = LegifranceDatabase(path=db_path)
    client = LegifranceClient(production=False)
    scrapper = LegifranceScrapper()
    database.create_database(overwrite=db_reset,exist_ok=True)
    law_text_dict = client.list_lawtexts(law_names)
    existing_law_texts = database.get_all_lawtexts()
    # We create lawtexts
    created_lawtexts = []
    for law_text in law_text_dict.values():
        if law_text not in existing_law_texts:
            database.add_lawtext(law_text)
            created_lawtexts.append(law_text)
    database.commit()
    
    # We only update sections for newly created...
    for i,law_text in enumerate(created_lawtexts):
        law_text:LawText
        sections = client.get_lawtext(law_text)
        law_text.sections = sections
        database.commit()
        all_sections_dict = law_text.get_all_sections()
        # We now download articles...
        p_bar = tqdm(all_sections_dict.values(),desc=law_text.title)
        for section in p_bar:
            postfix={}
            section:Section
            # We only want to pull empty..
            num_incomplete = database.session.query(func.count(Article.id)).where(
                and_(
                    Article.section_id==section.id,
                    Article.content.is_(None)
                )
            ).scalar()
            is_root = (section.section_id is None)
            if num_incomplete>0 or is_root:
                # If is_empty, we are on a root that gather more article at once... 
                article_list=scrapper.get_section(section_legi_id=section.legi_id,text_legi_id=law_text.legi_id)
                # We only keep releavant articles for completion...
                articles_to_complete = database.session.query(Article).where(
                    and_(
                        Article.legi_id.in_([a['legi_id'] for a in article_list]),
                        Article.content.is_(None))).order_by(Article.legi_id).all()
                if len(articles_to_complete)>0:
                    article_instances = {a.legi_id:a for a in articles_to_complete}
                    article_list = [a for a in article_list if a['legi_id'] in article_instances]
                    
                    for i,article_dict in enumerate(article_list):
                        # We get the right instance.
                        article = article_instances[article_dict['legi_id']]
                        postfix.update({'article':f"{i+1}/{len(article_list)}",'title':'None'})
                        if article is not None:
                            article:Article                            
                            title = f"{law_text.title} - {article_dict['title']}"
                            article.title = title
                            article.empty = False
                            article.active = not article_dict['is_abrogated']
                            article.content = article_dict['content']
                            postfix.update({'title':article_dict['title']})
                        p_bar.set_postfix(**postfix)
                    database.commit()



if __name__=='__main__':
    args = parser.parse_args()
    main(**vars(args))