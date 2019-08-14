import base64
import json
from datetime import datetime
from http.cookiejar import MozillaCookieJar
from os import getcwd
from pathlib import Path
from typing import Dict, List
from urllib.error import HTTPError
from urllib.parse import urlencode, urlunsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener


class EnergySession:
    base_url = 'game.energy.ch'
    api_root = '/api'
    protocol = 'https'

    def __init__(self):
        cookie_file = Path(getcwd()) / 'cookies.txt'
        self.cookie_jar = MozillaCookieJar(str(cookie_file))
        self.cookie_jar.load()

        self.session = build_opener(HTTPCookieProcessor(self.cookie_jar))
        self.last_response = None

    @property
    def phone_number(self) -> str:
        return self._jwt_data().get('sub')

    @property
    def expiry(self) -> datetime or None:
        timestamp = self._jwt_data().get('exp')
        return datetime.utcfromtimestamp(timestamp) if timestamp else None

    def smstoken(self, mobile: str) -> bool:
        endpoint = 'smstoken'

        data = {
            'mobile': mobile,
        }

        response_data = self._request(endpoint=endpoint, data=data, method='POST')
        return response_data.get('status') == 'ok'

    def login(self, mobile: str, token: str) -> bool:
        endpoint = f'smstoken/{token}'

        data = {
            'mobile': mobile,
        }

        try:
            response_data = self._request(endpoint=endpoint, data=data, method='PUT')
        except HTTPError as e:
            response_data = e.peek()
            data = json.loads(response_data)
            if data.get('code') == 403 and data.get('errorName') == 'InvalidToken':
                return False
            raise e
        return bool(response_data.get('token'))

    def logout(self):
        self.cookie_jar.clear()

    def questions(self) -> List[Dict]:
        endpoint = 'questions'

        return self._request(endpoint=endpoint)

    def check_questions(self, answers: List[int], auto_check_win: bool = True) -> bool:
        endpoint = 'questions/check'

        data = {
            'answers': answers
        }

        response = self._request(endpoint=endpoint, data=data, method='POST')
        check = response.get('correct')

        if auto_check_win and check:
            return self.check_win()
        return check

    def check_win(self) -> bool:
        endpoint = 'win'

        data = {
            'name': "eair",
            'isTicketGame': True
        }

        response = self._request(endpoint=endpoint, data=data, method='POST')
        return response.get('win')


    def _jwt_data(self) -> Dict:
        token = None
        for cookie in self.cookie_jar:
            if cookie.name != 'jwt-token':
                continue
            token = cookie.value
        if not token:
            return {}
        data = token.split('.')[1]
        return json.loads(base64.decodebytes(data.encode())) or {}

    def _build_url(self, endpoint: str, parameters: Dict = None) -> str:
        query = urlencode(parameters or {})
        return urlunsplit((self.protocol, self.base_url, f'{self.api_root}/{endpoint}', query, ''))

    def _request(self, *, endpoint: str, data: Dict = None, params: Dict = None, method: str = None) -> Dict or List:
        method = method or 'GET'

        url = self._build_url(endpoint, params)

        encoded_data = urlencode(data).encode() if data else None
        request = Request(url, method=method, data=encoded_data, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/76.0.3809.87 Safari/537.36'
        })

        request.origin_req_host = f'{self.protocol}://{self.base_url}'
        self.last_response = self.session.open(request)
        self.cookie_jar.save()

        return json.loads(self.last_response.peek())
