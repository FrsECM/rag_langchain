from bs4 import BeautifulSoup
import requests
import re


class LegifranceScrapper():
    def __init__(self) -> None:
        self.session = requests.session()

    def get_section(self,section_legi_id:str,text_legi_id:str):
        url = f"https://www.legifrance.gouv.fr/codes/section_lc/{text_legi_id}/{section_legi_id}/"
        response = self.session.get(url)
        page_html = response.text
        soup = BeautifulSoup(page_html, 'lxml')
        articles = soup.find_all('article')
        articles_result = []
        for article in articles:
                article:BeautifulSoup
                desc = article.find(class_='name-article')
                legi_id = desc.attrs['data-anchor']
                title = desc.get_text().strip()
                is_abrogated=False
                if '(abrogé)' in title:
                     is_abrogated=True
                     
                content_root = article.find(class_='content')
                content_paragraphs = content_root.find_all('p')
                content = ""
                for paragraph in content_paragraphs:
                    content+=paragraph.get_text()+'\n'                
                content=content.strip()
                article = {'legi_id':legi_id,'content':content,'title':title,'is_abrogated':is_abrogated}
                articles_result.append(article)
        return articles_result
    