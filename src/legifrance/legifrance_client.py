import requests
import os
import json
from datetime import datetime,timedelta
from typing import List
from .orm import LawText


class LegifranceClient:
    def __init__(self,client_id:str=None,client_secret:str=None):
        self.client_id = os.getenv("PISTE_CLIENT_ID") if client_id is None else client_id        
        self.client_secret = os.getenv("PISTE_CLIENT_SECRET") if client_secret is None else client_secret
        self.base_url = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"
        self.authentication_url = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
        self.token=None
        self.token_expiration=None

    @property
    def headers(self):
        now = datetime.now()
        if self.token is None or now>=self.token_expiration:
            self._refresh_token()

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
        response = requests.post(
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
    
    def list_lawtexts(self,query:str='code civil')->List[LawText]:
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
        response = requests.post(
            url=api_url,
            data=payload,
            headers=self.headers
        )
        return [LawText.from_json(t) for t in response.json()['results']]


