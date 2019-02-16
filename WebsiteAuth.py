import requests
from bs4 import BeautifulSoup
import os
from PyQt5.QtCore import pyqtSignal, QRunnable


class AuthSession(QRunnable):
    def __init__(self):
        super(AuthSession, self).__init__()
        self.headers = {'Referer': 'https://freesound.org/home/login/?next=/',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'}
        self.login_data = {}
        self.download_canceled = False
        self.url = ''
        self.session = None
        self.token_id_form = []
        self.signals = DownloaderSigs()
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

    def get_sound_page_html(self, url):
        response = self.session.get(url, headers=self.headers)
        return response.content

    def get_sound_link(self, url):
        return self.find_sound_url(self.get_sound_page_html(url))

    def set_token_id(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        attr_type = self.token_id_form[2]
        tag_type = self.token_id_form[1]
        attr_value = self.token_id_form[0]
        self.login_data[attr_value] = soup.find(tag_type, attrs={attr_type: attr_value})['value']

    def download_sound(self, url):
        url_title = url[url.rfind('/') + 1:]
        file_download_path = f'{self.download_folder}\\{url_title}'
        amount = 1024 * 200
        fd = open(file_download_path, 'wb')
        r = self.session.get(url, stream=True)
        self.signals.download_started.emit()
        for chunk in r.iter_content(amount):
            if self.download_canceled:
                fd.close()
                self.remove(file_download_path)
                break
            fd.write(chunk)
            # self.signals.downloaded.emit()
        if not self.download_canceled:
            fd.close()
            self.signals.download_done.emit(file_download_path)
        else:
            fd.close()
            self.remove(file_download_path)

    def remove(self, path):
        os.remove(path)


class FreeSound(AuthSession):
        def __init__(self, username, password):
            super(FreeSound, self).__init__()
            self.url = 'https://freesound.org/home/login/?next=/'
            self.token_id_form = ['csrfmiddlewaretoken', 'input', 'name']
            self.login_data = {'username': username, 'password': password}
            self.login()
            self.base_url = 'http://freesound.org'

        def find_sound_url(self, html):
            s = BeautifulSoup(html, 'html.parser')
            return self.base_url + s.find('a', attrs={'id': 'download_button'})['href']
