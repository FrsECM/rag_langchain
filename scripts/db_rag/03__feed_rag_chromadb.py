import argparse
from src.legifrance import LegifranceDatabase
from src.legifrance.orm import Article,LawText
from src.rag import CHROMA_RAG
from datetime import datetime
from tqdm.auto import tqdm

parser = argparse.ArgumentParser()
parser.add_argument('--db_path',default='data/sqlite/legifrance.db')
## Notaire
# parser.add_argument('--rag_path',default='data/chroma_notaire/')
# parser.add_argument('--lawtext_queries',default='urbanisme|impôt|rural|Code civil|forestier|commune|tourisme')
# Travail
parser.add_argument('--rag_path',default='data/chroma_travail/')
parser.add_argument('--lawtext_queries',default='travail|impôt')
# Pénal
parser.add_argument('--rag_path',default='data/chroma_travail/')
parser.add_argument('--lawtext_queries',default='pénal|pénitanciaire')


def main(db_path:str,rag_path:str,lawtext_queries:str):
    db = LegifranceDatabase(db_path)
    rag = CHROMA_RAG(rag_path)
    for query in lawtext_queries.split('|'):
        lawtexts = db.get_lawtexts(query)
        for lawtext in lawtexts:
            lawtext:LawText
            articles = lawtext.get_all_articles()
            articles = [a for a in articles if a.active]
            texts=[]
            metadatas = []
            for article in tqdm(articles,desc=lawtext.title):
                def str_date(date:datetime):
                    if date is not None:
                        return date.strftime('%Y-%m-%d')
                    else:
                        return 'None'
                def force_type(input):
                    if isinstance(input,(float,int,bool,str)):
                        return input
                    if input is None:
                        return ''
                    else:
                        raise Exception('type incompatible with vector database...')

                metadata = {
                    'source':force_type(article.title),
                    'active':force_type(article.active),
                    'code': force_type(lawtext.title),
                    'start_date':str_date(article.start_date),
                    'end_date':str_date(article.end_date),
                    'content':force_type(article.content),
                    'nota':force_type(article.nota)
                }
                text = f"{force_type(article.content)}\n{force_type(article.nota)}"
                texts.append(text)
                metadatas.append(metadata)
            documents = rag.create_documents(texts,metadatas)
            rag.add_documents(documents,lawtext.title)
    
    

    print('terminé')

if __name__ == '__main__':
    args = parser.parse_args()
    main(**vars(args))