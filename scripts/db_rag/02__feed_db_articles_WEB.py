from src.legifrance import LegifranceDatabase
from src.legifrance.legifrance_scrapper import LegifranceScrapper
from src.legifrance.orm import Article,Section,LawText
from sqlalchemy import select,and_,Row,or_,func
import argparse
from tqdm.auto import tqdm
import asyncio

parser = argparse.ArgumentParser()
parser.add_argument('--db_path',default='data/sqlite/legifrance.db')
parser.add_argument('--text_name_or_id',default="Code")
parser.add_argument('--update_articles',action='store_true',default=True)
parser.add_argument('--force_root',action='store_true',default=True)


def main(db_path:str,text_name_or_id:str,update_articles:bool,force_root:bool):
    database = LegifranceDatabase(path=db_path)
    scrapper = LegifranceScrapper()
    db_lawtexts = database.session.query(LawText).where(
        or_(
            LawText.title.contains(text_name_or_id),
            LawText.legi_id.contains(text_name_or_id)
            )
    ).all()

    # We only update newly created...
    if update_articles:
        for text in db_lawtexts:
            text:LawText
            # We indexed by article then it will be fast...
            sections = text.get_all_sections()
            # We put in first "root" sections
            # It's because it's faster to load first pages with a lot of articles...
            # Other pages will not be required because articles will be already completed.
            root_sections = database.session.query(Section).where(Section.lawtext_id==text.id).all()
            for section in root_sections:
                sections.remove(section)
                sections.insert(0,section)
            
            p_bar = tqdm(sections,desc=text.title)
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
                is_root = (section.lawtext_id == text.id and force_root)
                if num_incomplete>0 or is_root:
                    # If is_empty, we are on a root that gather more article at once... 
                    article_list=scrapper.get_section(section_legi_id=section.legi_id,text_legi_id=text.legi_id)
                    # We only keep releavant articles for completion...
                    articles_to_complete = database.session.query(Article).where(
                        and_(
                            Article.legi_id.in_([a['legi_id'] for a in article_list]),
                            Article.content.is_(None))).order_by(Article.legi_id).all()
                    article_instances = {a.legi_id:a for a in articles_to_complete}
                    article_list = [a for a in article_list if a['legi_id'] in article_instances]
                    
                    for i,article_dict in enumerate(article_list):
                        # We get the right instance.
                        article = article_instances[article_dict['legi_id']]
                        postfix.update({'article':f"{i+1}/{len(article_list)}",'title':'None'})
                        if article is not None:
                            article:Article                            
                            title = f"{text.title} - {article_dict['title']}"
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