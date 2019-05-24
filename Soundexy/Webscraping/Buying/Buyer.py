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
        self.headers = {'Referer': 'https://download.prosoundeffects.com/',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'}

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
        item_time = round(time.time())
        temp_data = {'item': {"type": "licensing", "item_id": f"{item['id']}-95-0", "track_id": item['id'],
                              "track": item, "license": [{"title": "Royalty Free", "price": 5,
                                                          "description": "This license allows you to use this sound in any project, commercial or otherwise.",
                                                          "key": "0", "agreement": 44}], "project": [], "price": 5,
                              "affiliate": None, "time": item_time,
                              "index": f"1_{item_time}"}}
        other_more_different_temp_data = {'item': {"type":"licensing","item_id":"17779649-95-0","track_id":17779649,"track":{"id":17779649,"title":"CW002_Moody_Winds_Vast_Dark_Whistling.wav","date":"03/27/2017","length":"1:33","actualLength":93.42933333,"plays":"21,226","downloads":"241","comments":[],"genres":[{"id":279196,"name":"Winds"}],"tempos":[{"id":316,"name":"Unspecified"}],"cueTypes":[{"id":195,"name":"Songs"}],"bpm":0,"catalog":{"id":675,"name":"Pro Sound Effects","image":"https://dm09pscvq9wc9.cloudfront.net/user_data/33375/1415659937-33375-150.png"},"label":{"id":640628,"name":"Pro Sound Effects","image":"https://dm09pscvq9wc9.cloudfront.net/user_data/33375/1415659937-33375-150.png"},"artist":{"id":390407,"name":"Ann Kroeber, Alan Splet","description":"","image":"images/shared/default_artist6.jpg"},"composer":{"id":0,"name":"","image":"images/shared/default_artist6.jpg"},"publisher":{"id":0,"name":""},"writers":[],"publishers":[],"album":{"id":4084354,"name":"Cinematic Winds","image":"https://dm09pscvq9wc9.cloudfront.net/user_data/117653/1552595751-117653-r.jpg","code":"","number":"0"},"key":{"id":0,"name":"Unspecified","minorId":0},"has_vocal":2,"explicit":2,"isrc":"","iswc":"","workNumbers":[],"featured":17,"userDownloaded":0,"userLastDLdate":0,"private":0,"styles":[],"moods":[],"description":"Vast Dark Whistling Winds, Deep Howl, Slow Tonal Whistling","keywords":"","instruments":"","version":"","formats":{"mp3":0,"wav":27043426,"aiff":0,"extras":[],"disableMp3":0,"disableWav":0,"disableAiff":0},"file":{"waveform":"https://sourceaudio.s3.amazonaws.com/1/7/7/7/9/6/4/9/17779649.js","playHtml5":"https://d1ombmsyi1byit.cloudfront.net/1/7/7/7/9/6/4/9/17779649-128.mp3","waveformCallbackId":17779649,"filename":"CW002_Moody_Winds_Vast_Dark_Whistling.mp3"},"custom_fields":[{"id":17,"name":"Library","value":"Cinematic Winds","hidden":0},{"id":104,"name":"Designer","value":"Ann Kroeber, Alan Splet","hidden":0},{"id":359,"name":"Duration","value":"01:33.4","hidden":0}],"can_download":0,"masterId":17779649,"alternates":[],"alternateCount":0,"alternateDownloadFormats":[],"price":-1,"tagged":0,"user_projects":[],"user_cue_sheets":[],"dateAddedToBank":1558729302921},"license":[{"title":"Royalty Free","price":5,"description":"This license allows you to use this sound in any project, commercial or otherwise.","key":"0","agreement":44}],"project":[],"price":5,"affiliate":None,"time":1558729312,"index":"1_1558729312"}}
        url = "https://download.prosoundeffects.com/ajax.php?p=shopping_cart&action=add_to_cart"
        data = {"type": "license", 'item_id': f'{self.sound_id}-95-0', 'sound_id': self.sound_id, 'track': item}
        print(self.headers)
        return self.session.post(url, data=other_more_different_temp_data, headers=self.headers)

    def checkout(self):
        url = "https://download.prosoundeffects.com/ajax.php?p=purchaser&action=load&key=licensing&useWhite=true"
        data = {'cartItems': self.set_all_tracks_to_track_id(self.get_cart().json()['content']['items']), 'channelId':
                ''}
        print(data)
        return self.session.post(url, data=data, headers=self.headers)

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


buyer_session = WebsiteAuth.ProSound()
buyer = ProSoundBuyer(18335915, buyer_session)
print(buyer.checkout().json())
