from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import quote
from typing import Dict,List


class LegifranceScrapper():
    def __init__(self) -> None:
        self.session = requests.session()

    def list_codes(self,text_or_id:str):
        """List code  from a query...

        Args:
            text_or_id (str): _description_

        Returns:
            _type_: _description_
        """
        text_queries = text_or_id.split('|')
        # We use a dict in order to avoid duplicates....
        code_results = {}
        for text_query in text_queries:
            url = f"https://www.legifrance.gouv.fr/liste/code"
            url +=f"?codeTitle={quote(text_query,safe='')}"
            url +="&etatTexte=VIGUEUR_NON_ETEN&etatTexte=VIGUEUR"
            response = self.session.get(url)
            page_html = response.text
            soup = BeautifulSoup(page_html, 'lxml')
            code_list = soup.find(class_='code-list')
            codes = code_list.find_all('li')
            for code in codes:
                item = code.find('a')
                title = item.get_text() # title of the convention
                legi_id = item.attrs['id']
                if str(legi_id).startswith('id'):
                    legi_id = str(legi_id[2:])
                code = dict(title=title,legi_id=legi_id)
                code_results[legi_id]=code
        # We drop return it as a list
        return list(code_results.values())

    def list_code_sections(self,code_id:str):
        url = f"https://www.legifrance.gouv.fr/codes/texte_lc/{code_id}"
        response = self.session.get(url)
        page_html = response.text
        section_dict = {}
        soup = BeautifulSoup(page_html, 'lxml')
        root_sections = soup.find(id='liste-sommaire').find_all('li',recursive=False)

        def parse_article(article_soup:BeautifulSoup):
            article = article_soup.find('a')
            legi_id = article.attrs['id']
            if legi_id.startswith('art'):
                legi_id=legi_id[3:]
            title = article.get_text().strip()
            return dict(legi_id=legi_id,title=title)
        def parse_section(section_soup:BeautifulSoup):
            section_info = section_soup.find('a')
            if section_info is None:
                section_info = section_soup.find('span')

            legi_id = section_info.attrs['id']
            title = re.sub(r"\(Articles \d+.*?\)", "", section_info.get_text())
            sections = []
            articles = []

            # In case we have articles, we have a child section...
            childs = section_soup.find('div',class_='js-child')
            if childs is not None:
                # what we do when we have a div (we have articles or articles + sub_sections)
                sub = childs.find_all('ul',recursive=False)
                articles = sub[0].find_all('li',recursive=False)
                if len(sub)>1:
                    sections = sub[1].find_all('li',recursive=False)
            else:
                # In case we don't have child_section, we can have sub_sections.
                sub_soup = section_soup.find('ul',class_='js-child')
                if sub_soup is not None:
                    sections = sub_soup.find_all('li',recursive=False)
            sections = [parse_section(s) for s in sections]
            articles = [parse_article(a) for a in articles]
            return dict(legi_id=legi_id,title=title,sections=sections,articles=articles)
                
        for section in root_sections:
            section_dict.update(parse_section(section))
        return section_dict
    
    def list_conventions(self,text_or_id:str)->List[dict]:
        """List collective convention based from a query...

        Args:
            text_or_id (str): _description_

        Returns:
            _type_: _description_
        """
        text_queries = text_or_id.split('|')
        # We use a dict in order to avoid duplicates....
        conventions_result = {}
        for text_query in text_queries:
            url = f"https://www.legifrance.gouv.fr/liste/idcc"
            url +=f"?titre_suggest={quote(text_query,safe='')}"
            url +="&facetteEtat=VIGUEUR_NON_ETEN&facetteEtat=VIGUEUR&facetteEtat=VIGUEUR_ETEN&sortValue=DATE_UPDATE"
            response = self.session.get(url)
            page_html = response.text
            soup = BeautifulSoup(page_html, 'lxml')
            conventions = soup.find_all('article')
            for convention in conventions:
                item = convention.find(class_='title-convention')
                title = item.get_text() # title of the convention
                legi_id = item.attrs['id']
                if str(legi_id).startswith('id'):
                    legi_id = str(legi_id[2:])
                convention = dict(title=title,legi_id=legi_id)
                conventions_result[legi_id]=convention
        # We drop return it as a list
        return list(conventions_result.values())
    
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
    