import requests
from bs4 import BeautifulSoup
from PyQt5.QtCore import QRunnable
import base64
from lxml import html as lxml_html


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
        key_url = f"https://download.prosoundeffects.com/download.php"
        params = {'track_id': result.original_id, 'type': 'wav', 'source': 'details'}
        return self.session.get(key_url, params=params, headers=self.headers, allow_redirects=False).headers['location']

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
        print(key_url)
        return key_url

    def login(self):
        with requests.Session() as s:
            self.session = s
            r = s.post(self.url, self.login_data, headers=self.headers)
            html = lxml_html.fromstring(r.content)
            if len(html.xpath('//font')) > 0:
                raise LoginError("Incorrect Credentials")
            self.session = s


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
