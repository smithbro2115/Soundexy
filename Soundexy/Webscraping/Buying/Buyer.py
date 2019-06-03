from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QRunnable
import requests
import time
from Soundexy.Webscraping.Authorization import WebsiteAuth


class BuyerSigs(QObject):
    credit_card_error = pyqtSignal(str)
    error = pyqtSignal(str)
    started = pyqtSignal()
    finished = pyqtSignal()


class Buyer(QRunnable):
    def __init__(self, sound_id, session):
        super(Buyer, self).__init__()
        self.signals = BuyerSigs()
        self.sound_id = sound_id
        self.session = session
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'}
        self.encoded_headers = self.headers
        self.encoded_headers['Content-type'] = 'application/x-www-form-urlencoded'

    @pyqtSlot()
    def run(self):
        pass

    def buy_sound(self):
        pass


class ProSoundBuyer(Buyer):
    def __init__(self, sound_id, session):
        super(ProSoundBuyer, self).__init__(sound_id, session)
        self.headers['Content-type'] = 'application/x-www-form-urlencoded'

    def add_to_cart(self):
        item = self.get_original_item()
        url = "https://download.prosoundeffects.com/ajax.php?p=shopping_cart&action=add_to_cart"
        data = {"type": "license", 'item_id': f'{self.sound_id}-95-0', 'sound_id': self.sound_id, 'track': item}
        return self.session.post(url, json=data, headers=self.encoded_headers)

    def checkout(self):
        url = "https://download.prosoundeffects.com/ajax.php?p=purchaser&action=load&key=licensing&useWhite=true"
        data = {'cartItems': self.set_all_tracks_to_track_id(self.get_cart().json()['content']['items']), 'channelId':
                ''}
        print(self.encoded_headers)
        return self.session.post(url, json=data, headers=self.encoded_headers)

    def set_all_tracks_to_track_id(self, items):
        for item in items:
            item['track'] = {'track_id': item['track']['id']}
        return items

    def get_original_item(self):
        url = f"https://download.prosoundeffects.com/ajax.php?p=track_info&customs=1&id={self.sound_id}"
        return self.session.get(url, headers=self.headers).json()['content'][1]

    def get_cart(self):
        url = "https://download.prosoundeffects.com/ajax.php?p=shopping_cart&action=get_cart_contents"
        return self.session.get(url, headers=self.headers)

    def clear_cart(self):
        url = "https://download.prosoundeffects.com/ajax.php?p=shopping_cart&action=clear_cart"
        return self.session.get(url, headers=self.headers)


buyer_session = WebsiteAuth.ProSound('smithbro2115@gmail.com', 'Ferrari578')
buyer = ProSoundBuyer(16514748, buyer_session)
print(buyer.checkout().json())
