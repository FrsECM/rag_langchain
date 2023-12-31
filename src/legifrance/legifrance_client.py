import requests
import os
import json
from datetime import datetime,timedelta
from typing import List,Dict
from .orm import LawText,Section,Article,CollectiveConvention
from tqdm.auto import tqdm
import time
import re 

class LegifranceClient:
    def __init__(self,client_id:str=None,client_secret:str=None,production:bool=False,api_limit_per_second:int=None):
        if production:
            self.client_id = os.getenv("PISTE_PROD_CLIENT_ID") if client_id is None else client_id        
            self.client_secret = os.getenv("PISTE_PROD_CLIENT_SECRET") if client_secret is None else client_secret
            self.base_url = "http://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
            self.authentication_url = "https://oauth.piste.gouv.fr/api/oauth/token"
            self.api_limit_per_sec = 20
        else:
            self.client_id = os.getenv("PISTE_SANDBOX_CLIENT_ID") if client_id is None else client_id        
            self.client_secret = os.getenv("PISTE_SANDBOX_CLIENT_SECRET") if client_secret is None else client_secret
            self.base_url = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"
            self.authentication_url = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
            self.api_limit_per_sec = 2
        if api_limit_per_second is not None:
            self.api_limit_per_sec = api_limit_per_second
        self.token=None
        self.token_expiration=None
        # https://stackoverflow.com/questions/51600489/why-does-a-request-via-python-requests-takes-almost-seven-times-longer-than-in
        self.request_session = requests.Session()
    @property
    def headers(self):
        now = datetime.now()
        if self.token is None or now>=self.token_expiration:
            self._refresh_token()
        # We wait to respect the api limit.
        time.sleep(1./self.api_limit_per_sec)
        header = {
            'Content-Type': 'application/json',
            "Authorization": f"Bearer {self.token}"
            }
        return header

    def _refresh_token(self):
        """Refresh the token from PISTE API
        
        https://developer.aife.economie.gouv.fr/


        Raises:
            Exception: Issue to get the token.
        """
        data = {
            'grant_type': 'client_credentials', 
            'client_id': self.client_id,
            'client_secret':self.client_secret,
            'scope':'openid'
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = self.request_session.post(
            url=self.authentication_url,
            headers=headers,
            data=data
        )
        if response.status_code == 200:
            content = response.json()
            
            self.token=content['access_token']
            self.token_expiration = datetime.now()+timedelta(seconds=content['expires_in']-1)
        else:
            raise Exception(f'Response {response.status_code}\nToken unavailable with provided credentials\n{data}')
    
    def list_lawtexts(self,query:str='code civil')->Dict[str,LawText]:
        text_queries = query.split('|')
        law_texts =[]
        for query in text_queries:
            api_url = f"{self.base_url}/list/code"
            payload = json.dumps({
                "pageSize": 50,
                "sort": "TITLE_ASC",
                "pageNumber": 1,
                "codeName": query,
                "states": [
                    "VIGUEUR"
                ]
            })
            response = self.request_session.post(
                url=api_url,
                data=payload,
                headers=self.headers
            )
            law_texts.extend([LawText.from_json(t) for t in response.json()['results']])
        law_texts:List[LawText]
        law_texts_dict = {l.legi_id:l for l in law_texts}
        
        return law_texts_dict
    
    def get_lawtext(self,lawtext:LawText,search:str="",progress=True)->List[Section]:
        if progress:
            s_bar = tqdm(desc=lawtext.title)
        api_url = f"{self.base_url}/consult/code"
        payload = json.dumps({
            "textId": lawtext.legi_id,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "sctCid": lawtext.legi_id,
            "abrogated": False,
            "searchedString": search,
            "fromSuggest": False
        })
        response = self.request_session.post(
            url=api_url,
            data=payload,
            headers=self.headers
        )
        sections = response.json()['sections']
        if progress:
            s_bar.total = len(sections)
            result = []
            for section in sections:
                result.append(Section.from_json(section))
                s_bar.update(1)
            return result
        return [Section.from_json(t) for t in s_bar]

    def get_convention(self,convention:CollectiveConvention,progress=True)->CollectiveConvention:
        if progress:
            s_bar = tqdm(desc=convention.title)
        api_url = f"{self.base_url}/consult/kaliText"
        payload = json.dumps({
            "id": convention.legi_id,
            "searchedString": ""
            })
        response = self.request_session.post(
            url=api_url,
            data=payload,
            headers=self.headers
        )
        response_json = response.json()
        sections_json = response_json['sections']
        articles_json = response_json['articles']
        if progress:
            s_bar.total = len(sections_json)+len(articles_json)
        sections = []
        articles = []
        for s in sections_json:
            sections.append(Section.from_json(s))
            if progress:
                s_bar.update(1)
        for a in articles_json:
            articles.append(Article.from_json(a))
            if progress:
                s_bar.update(1)
        convention.articles = articles
        convention.sections = sections
        return convention

    def get_article_dict(self,article_legi_id:str)->dict:
        api_url = f"{self.base_url}/consult/getArticleByCid"
        payload = json.dumps({
            "cid": article_legi_id
        })
        response = self.request_session.post(
            url=api_url,
            data=payload,
            headers=self.headers
        )
        json_response=response.json()
        if 'listArticle' in json_response:
            article_dict_list = response.json()['listArticle']
            if len(article_dict_list)>0:
                article_dict = article_dict_list[0] # Last version of the article...
                return article_dict
        return None
    
    def update_article(self,article:Article)->Article:
        api_url = f"{self.base_url}/consult/getArticleByCid"
        payload = json.dumps({
            "cid": article.legi_id
        })
        response = self.request_session.post(
            url=api_url,
            data=payload,
            headers=self.headers
        )
        article_dict_list = response.json()['listArticle']
        if len(article_dict_list)>0:
            article_dict = article_dict_list[0] # Last version of the article...
            article.update(article_dict)
        else:
            article.active=False
        return article