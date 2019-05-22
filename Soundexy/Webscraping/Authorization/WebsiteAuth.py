import requests
from bs4 import BeautifulSoup
from PyQt5.QtCore import QRunnable
import base64


class LoginError(Exception):
    pass


class AuthSession(QRunnable):
    def __init__(self, username, password):
        super(AuthSession, self).__init__()
        self.headers = {'Referer': 'https://freesound.org/home/login/?next=/',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'}
        self.login_data = {'username': username, 'password': password}
        self.download_canceled = False
        self.url = ''
        self.session = None
        self.token_id_form = []
        self.download_folder = 'downloads'  # change to a config

    def login(self):
        with requests.Session() as s:
            self.session = s
            r = s.get(self.url, headers=self.headers)
            self.set_token_id(r.content)
            s.post(self.url, headers=self.headers, data=self.login_data)
            self.session = s

    def find_sound_url(self, url):
        return ''

    def get_sound_link(self, result):
        return self.find_sound_url(result)

    def set_token_id(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        attr_type = self.token_id_form[2]
        tag_type = self.token_id_form[1]
        attr_value = self.token_id_form[0]
        self.login_data[attr_value] = soup.find(tag_type, attrs={attr_type: attr_value})['value']

    def get(self, url, **kwargs):
        return self.session.get(url, **kwargs)

    def get_content_disposition(self, r):
        return r.headers['Content-disposition']


class FreeSound(AuthSession):
        def __init__(self, username, password):
            super(FreeSound, self).__init__(username, password)
            self.url = 'https://freesound.org/home/login/?next=/'
            self.token_id_form = ['csrfmiddlewaretoken', 'input', 'name']
            self.login()
            self.base_url = 'http://freesound.org'

        def get_sound_page_html(self, url):
            response = self.session.get(url, headers=self.headers)
            return response.content

        def find_sound_url(self, result):
            html = self.get_sound_page_html(result.meta_file['download link'])
            s = BeautifulSoup(html, 'html.parser')
            return self.base_url + s.find('a', attrs={'id': 'download_button'})['href']


class ProSound(AuthSession):
    def __init__(self, username, password):
        super(ProSound, self).__init__(username, password)
        self.url = 'https://download.prosoundeffects.com/ajax.php?p=login&action=login'
        self.login_data = {'email': username, 'password': base64.b64encode(password.encode())}
        self.login()
        self.base_url = 'https://download.prosoundeffects.com/ajax.php'

    def find_sound_url(self, result):
        key_url = f"https://download.prosoundeffects.com/download.php?track_id={result.original_id}&type=wav"
        return self.session.head(key_url, headers=self.headers).headers['location']

    def login(self):
        with requests.Session() as s:
            self.session = s
            r = s.post(self.url, self.login_data, headers=self.headers)
            try:
                if r.json()['content']['loginFailed']:
                    raise LoginError('Incorrect Credentials')
            except KeyError:
                pass
            self.session = s
