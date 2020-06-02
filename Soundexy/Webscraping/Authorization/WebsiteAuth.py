import requests
from bs4 import BeautifulSoup
from PyQt5.QtCore import QRunnable
import base64
from lxml import html as lxml_html
import re
import abc
import time
from Soundexy.Functionality.useful_utils import DictExpired, ExpiringDict
from Soundexy.Webscraping.Webscraping.WebScraperRequester import get_with_headers


class LoginError(Exception):
    pass


class AuthSession(QRunnable):
    def __init__(self, username, password):
        super(AuthSession, self).__init__()
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/74.0.3729.169 Safari/537.36'}
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

    def post(self, url, **kwargs):
        return self.session.post(url, **kwargs)

    def get_content_disposition(self, r):
        return r.headers['Content-disposition']


class FreeSound(AuthSession):
    def __init__(self, username, password):
        super(FreeSound, self).__init__(username, password)
        self.url = 'https://freesound.org/home/login/?next=/'
        self.headers['Referer'] = 'https://freesound.org/home/login/?next=/'
        self.token_id_form = ['csrfmiddlewaretoken', 'input', 'name']
        self.login()
        self.base_url = 'http://freesound.org'

    def get_sound_page_html(self, url):
        response = self.session.get(url, headers=self.headers)
        return response.content

    def find_sound_url(self, result):
        html = self.get_sound_page_html(result.meta_file['download_link'])
        s = BeautifulSoup(html, 'html.parser')
        return self.base_url + s.find('a', attrs={'id': 'download_button'})['href']


class ProSound(AuthSession):
    def __init__(self, username, password):
        super(ProSound, self).__init__(username, password)
        self.url = ProSoundAjaxNonceURL('https://download.prosoundeffects.com/ajax.php?p=login&action=login')
        self.login_data = {'email': username, 'password': base64.b64encode(password.encode())}
        self.login()
        self.base_url = 'https://download.prosoundeffects.com/ajax.php'

    def find_sound_url(self, result):
        key_url = f"https://download.prosoundeffects.com/download.php"
        params = {'track_id': result.original_id, 'type': 'wav', 'source': 'details'}
        return self.session.get(key_url, params=params, headers=self.headers, allow_redirects=False).headers['location']

    def login(self):
        with requests.Session() as s:
            self.session = s
            r = s.post(str(self.url), self.login_data, headers=self.headers)
            try:
                if r.json()['content']['loginFailed']:
                    raise LoginError('Incorrect Credentials')
            except KeyError:
                pass
            self.session = s


class SoundDogs(AuthSession):
    def __init__(self, username, password):
        super(SoundDogs, self).__init__(username, password)
        self.url = "https://www.sounddogs.com/signin/login"
        self.login_data = {'email': username, 'password': password}
        self.login()

    def regenerate_invoice_files(self, order, items):
        url = 'https://www.sounddogs.com/customer/regenerate_files'
        item_sound_formats = {}
        for item in items:
            item_sound_formats[item['id']] = 39
        post_data = {'invoiceId': order, 'itemSoundFormats': item_sound_formats}
        r = self.post(url, json=post_data)

    def find_sound_url(self, result):
        order, items = get_order_from_sound_dogs_sound(result.original_id, self)
        key_url = f"https://www.sounddogs.com/customer/download_invoice_item_sound?invoiceItemId=" \
            f"{get_item_from_order(result.original_id, items)['id']}"
        self.regenerate_invoice_files(order, items)
        return key_url

    def login(self):
        with requests.Session() as s:
            self.session = s
            r = s.post(self.url, self.login_data, headers=self.headers)
            html = lxml_html.fromstring(r.content)
            if len(html.xpath('//font')) > 0:
                raise LoginError("Incorrect Credentials")
            self.session = s


class AjaxNonceURL:
    ajax_credentials = ExpiringDict()
    time_of_last_nonce_generation = 0

    def __init__(self, base_url):
        self.base_url = base_url

    def __add__(self, other):
        return self.__str__() + other

    def __str__(self):
        try:
            return f"{self.base_url}&ajaxNonceKey={self.ajax_nonce_key}&ajaxNonce={self.ajax_nonce}"
        except DictExpired:
            self.__class__.ajax_credentials = {}

    @property
    def ajax_nonce_key(self):
        return self.get_credentials('ajaxNonceKey')

    @property
    def ajax_nonce(self):
        return self.get_credentials('ajaxNonce')

    def get_credentials(self, key):
        try:
            return self.ajax_credentials[key]
        except KeyError:
            self.__class__.ajax_credentials = self.fetch_credentials()
            self.__class__.time_of_last_nonce_generation = time.time()
            return self.get_credentials(key)

    @abc.abstractmethod
    def fetch_credentials(self) -> dict:
        pass


class ProSoundAjaxNonceURL(AjaxNonceURL):
    def fetch_credentials(self):
        raw_html = get_with_headers("https://download.prosoundeffects.com/").content
        return self.parse_nonce_credentials_from_raw_html(raw_html)

    def parse_nonce_credentials_from_raw_html(self, raw_html):
        tree = lxml_html.fromstring(raw_html)
        script_tags = tree.xpath('//head/script')
        for script_tag in script_tags:
            potential_credentials = self.parse_nonce_credentials_from_script_tag(script_tag)
            if potential_credentials:
                return potential_credentials

    @staticmethod
    def parse_nonce_credentials_from_script_tag(script_tag):
        script_string = lxml_html.tostring(script_tag).decode()
        if "Nonce" in script_string:
            strings = re.findall(r'"([A-Za-z0-9_\./\\-]*)"', script_string)
            ajax_nonce_credentials = {}
            for i, string in enumerate(strings):
                if string == "ajaxNonceKey":
                    ajax_nonce_credentials[string] = strings[i + 1]
                elif string == "ajaxNonce":
                    ajax_nonce_credentials[string] = strings[i + 1]
            return ajax_nonce_credentials


def get_item_from_order(sound_id, items):
    for item in items:
        if item['soundChannelId'] == int(sound_id):
            return item


def get_order_from_sound_dogs_sound(sound_id, auth_session):
    orders = get_all_orders_from_sound_dogs(auth_session)
    for order, items in orders.items():
        for item in items:
            if item['soundChannelId'] == int(sound_id):
                return order, items


def get_all_orders_from_sound_dogs(auth_session):
    raw_orders = get_all_sound_dog_orders(auth_session)
    orders = {}
    for order in raw_orders:
        if order['statusString'] == 'Charged':
            orders[order['id']] = order['invoiceItems']
    return orders


def get_all_sound_dog_orders(auth_session):
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    url = f"https://www.sounddogs.com/customer/order_history?page=0&orderType=0"
    r = auth_session.get(url, headers=headers)
    return r.json()['orders']
