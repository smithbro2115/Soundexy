from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QRunnable
from Soundexy.Webscraping.Authorization import WebsiteAuth

# test_item = {"id": 17779649, "title": "CW002_Moody_Winds_Vast_Dark_Whistling.wav", "date": "03/27/2017",
#              "length": "1:33", "actualLength": 93.42933333, "plays": "23,187", "downloads": "244", "comments": [],
#              "genres": [{"id": 279196, "name": "Winds"}], "tempos": [{"id": 316, "name": "Unspecified"}],
#              "cueTypes": [{"id": 195, "name": "Songs"}], "bpm": 0, "catalog": {"id": 675, "name": "Pro Sound Effects",
#                                                                                "image": "https://dm09pscvq9wc9.cloudfront.net/user_data/33375/1415659937-33375-150.png"},
#              "label": {"id": 640628, "name": "Pro Sound Effects",
#                        "image": "https://dm09pscvq9wc9.cloudfront.net/user_data/33375/1415659937-33375-150.png"},
#              "artist": {"id": 390407, "name": "Ann Kroeber, Alan Splet", "description": "",
#                         "image": "images/shared/default_artist6.jpg"},
#              "composer": {"id": 0, "name": "", "image": "images/shared/default_artist6.jpg"},
#              "publisher": {"id": 0, "name": ""}, "writers": [], "publishers": [],
#              "album": {"id": 4084354, "name": "Cinematic Winds",
#                        "image": "https://dm09pscvq9wc9.cloudfront.net/user_data/117653/1552595751-117653-r.jpg",
#                        "code": "", "number": "0"}, "key": {"id": 0, "name": "Unspecified", "minorId": 0},
#              "has_vocal": 2, "explicit": 2, "isrc": "", "iswc": "", "workNumbers": [], "featured": 17,
#              "userDownloaded": 0, "userLastDLdate": 0, "private": 0, "styles": [], "moods": [],
#              "description": "Vast Dark Whistling Winds, Deep Howl, Slow Tonal Whistling", "keywords": "",
#              "instruments": "", "version": "",
#              "formats": {"mp3": 0, "wav": 27043426, "aiff": 0, "extras": [], "disableMp3": 0, "disableWav": 0,
#                          "disableAiff": 0},
#              "file": {"waveform": "https://sourceaudio.s3.amazonaws.com/1/7/7/7/9/6/4/9/17779649.js",
#                       "playHtml5": "https://d1ombmsyi1byit.cloudfront.net/1/7/7/7/9/6/4/9/17779649-128.mp3",
#                       "waveformCallbackId": 17779649, "filename": "CW002_Moody_Winds_Vast_Dark_Whistling.mp3"},
#              "custom_fields": [{"id": 17, "name": "Library", "value": "Cinematic Winds", "hidden": 0},
#                                {"id": 104, "name": "Designer", "value": "Ann Kroeber, Alan Splet", "hidden": 0},
#                                {"id": 359, "name": "Duration", "value": "01:33.4", "hidden": 0}], "can_download": 0,
#              "masterId": 17779649, "alternates": [], "alternateCount": 0, "alternateDownloadFormats": [], "price": -1,
#              "tagged": 0, "user_projects": [], "user_cue_sheets": [], "dateAddedToBank": 1565892159896}
#
# test_post = {'item': {"type": "licensing", "item_id": "17779649-95-0", "track_id": 17779649,
#                       "track": {"id": 17779649, "title": "CW002_Moody_Winds_Vast_Dark_Whistling.wav",
#                                 "date": "03/27/2017", "length": "1:33", "actualLength": 93.42933333, "plays": "23,188",
#                                 "downloads": "244", "comments": [], "genres": [{"id": 279196, "name": "Winds"}],
#                                 "tempos": [{"id": 316, "name": "Unspecified"}],
#                                 "cueTypes": [{"id": 195, "name": "Songs"}], "bpm": 0,
#                                 "catalog": {"id": 675, "name": "Pro Sound Effects",
#                                             "image": "https://dm09pscvq9wc9.cloudfront.net/user_data/33375/1415659937-33375-150.png"},
#                                 "label": {"id": 640628, "name": "Pro Sound Effects",
#                                           "image": "https://dm09pscvq9wc9.cloudfront.net/user_data/33375/1415659937-33375-150.png"},
#                                 "artist": {"id": 390407, "name": "Ann Kroeber, Alan Splet", "description": "",
#                                            "image": "images/shared/default_artist6.jpg"},
#                                 "composer": {"id": 0, "name": "", "image": "images/shared/default_artist6.jpg"},
#                                 "publisher": {"id": 0, "name": ""}, "writers": [], "publishers": [],
#                                 "album": {"id": 4084354, "name": "Cinematic Winds",
#                                           "image": "https://dm09pscvq9wc9.cloudfront.net/user_data/117653/1552595751-117653-r.jpg",
#                                           "code": "", "number": "0"},
#                                 "key": {"id": 0, "name": "Unspecified", "minorId": 0}, "has_vocal": 2, "explicit": 2,
#                                 "isrc": "", "iswc": "", "workNumbers": [], "featured": 17, "userDownloaded": 0,
#                                 "userLastDLdate": 0, "private": 0, "styles": [], "moods": [],
#                                 "description": "Vast Dark Whistling Winds, Deep Howl, Slow Tonal Whistling",
#                                 "keywords": "", "instruments": "", "version": "",
#                                 "formats": {"mp3": 0, "wav": 27043426, "aiff": 0, "extras": [], "disableMp3": 0,
#                                             "disableWav": 0, "disableAiff": 0},
#                                 "file": {"waveform": "https://sourceaudio.s3.amazonaws.com/1/7/7/7/9/6/4/9/17779649.js",
#                                          "playHtml5": "https://d1ombmsyi1byit.cloudfront.net/1/7/7/7/9/6/4/9/17779649-128.mp3",
#                                          "waveformCallbackId": 17779649,
#                                          "filename": "CW002_Moody_Winds_Vast_Dark_Whistling.mp3"}, "custom_fields": [
#                               {"id": 17, "name": "Library", "value": "Cinematic Winds", "hidden": 0},
#                               {"id": 104, "name": "Designer", "value": "Ann Kroeber, Alan Splet", "hidden": 0},
#                               {"id": 359, "name": "Duration", "value": "01:33.4", "hidden": 0}], "can_download": 0,
#                                 "masterId": 17779649, "alternates": [], "alternateCount": 0,
#                                 "alternateDownloadFormats": [], "price": -1, "tagged": 0, "user_projects": [],
#                                 "user_cue_sheets": [], "dateAddedToBank": 1565892905307}, "license": [
#         {"title": "Royalty Free", "price": 5,
#          "description": "This license allows you to use this sound in any project, commercial or otherwise.",
#          "key": "0", "agreement": 44}], "project": [], "price": 5, "affiliate": None, "time": 1565892909,
#                       "index": "1_1565892909"}}


class BuyerSigs(QObject):
    credit_card_error = pyqtSignal(str)
    error = pyqtSignal(str)
    started = pyqtSignal()
    finished = pyqtSignal()


class Buyer(QRunnable):
    def __init__(self, sound_id, username, password):
        super(Buyer, self).__init__()
        self.signals = BuyerSigs()
        self.sound_id = sound_id
        self.error = None
        try:
            self.session = self.get_session_type()(username, password)
        except WebsiteAuth.LoginError as e:
            self.error = e
        else:
            self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'}
            self.encoded_headers = self.headers
            self.encoded_headers['Content-type'] = 'application/x-www-form-urlencoded'

    @pyqtSlot()
    def run(self):
        pass

    def buy_sound(self):
        pass

    def get_session_type(self):
        return WebsiteAuth.AuthSession


class SoundDogsBuyer(Buyer):
    @pyqtSlot()
    def run(self):
        if not self.error:
            self.add_to_cart(self.sound_id)
            self.signals.finished.emit()
        else:
            self.signals.error.emit(str(self.error))

    def add_to_cart(self, sound_id):
        url = f"https://www.sounddogs.com/basket/select/Sound/{sound_id}"
        self.session.get(url)

    def get_session_type(self):
        return WebsiteAuth.SoundDogs


# class ProSoundBuyer(Buyer):
#     def __init__(self, sound_id, username, password):
#         super(ProSoundBuyer, self).__init__(sound_id, username, password)
#         self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0'}
#
#     def get_session_type(self):
#         return WebsiteAuth.ProSound

    # def add_to_cart(self):
    #     item = self.get_original_item()
    #     consistent_time = time.time()
    #     item["dateAddedToBank"] = int(consistent_time*1000-1000)
    #     url = "https://download.prosoundeffects.com/ajax.php?p=shopping_cart&action=add_to_cart"
    #     data = {'item': {"type": "licensing", 'item_id': f'{self.sound_id}-95-0', 'track_id': self.sound_id,
    #                      'track': item, "license": [{"title": "Royalty Free", "price": 5,
    #                                                  "description": "This license allows you to use this sound in any project, commercial or otherwise.",
    #                                                  "key": "0", "agreement": 44}], "project": [], "price": 5,
    #                      "affiliate": None, "time": int(consistent_time), "index": f"1_{int(consistent_time)}"}}
    #     cookies_local = dict(self.session.session.cookies)
    #     # cookies_local['sa_user_secure_20151123'] = '$2y$12$G/sHA5KASkq5DQUN0Q48J.MO9r4iYfVVYpw15dcgV5vUIWki2Xdoe'
    #     # cookies_local['sa_user_normal'] = "111933;$2y$12$yFTHLKArlzvllR1KK9F3Qu5q/x4lS8PuaCkrypIK6l7gMYmm2TtOG"
    #     old = {'sa_user_normal': '111933;$2y$12$QA2xNW5SFkrIawYm/93rBuBlApDwLRa.9GLAMAChzct1sQYlkf9rO',
    #            'sa_user_secure_20151123': '$2y$12$hxccM1TdYSGy3G1K9zvRaOj0PCdoUmHjMglxgxek5QGT.dt61Nj7y',
    #            'PHPSESSID': 'or8jfm2rgm2rpvloto2icg6m80'}
    #     print(json.dumps(data))
    #     return self.session.post(url, data=test_post, headers=self.headers, cookies=cookies_local)
#
#     def checkout(self):
#         url = "https://download.prosoundeffects.com/ajax.php?p=purchaser&action=load&key=licensing&useWhite=true"
#         data = {'cartItems': self.set_all_tracks_to_track_id(self.get_cart().json()['content']['items']), 'channelId':
#                 ''}
#         print(self.encoded_headers)
#         return self.session.post(url, json=data, headers=self.encoded_headers)
#
#     def set_all_tracks_to_track_id(self, items):
#         for item in items:
#             item['track'] = {'track_id': item['track']['id']}
#         return items

    # def get_original_item(self):
    #     url = f"https://download.prosoundeffects.com/ajax.php?p=track_info&customs=1&id={self.sound_id}"
    #     return self.session.get(url, headers=self.headers).json()['content'][1]
    #
    # def get_cart(self):
    #     url = "https://download.prosoundeffects.com/ajax.php?p=shopping_cart&action=get_cart_contents"
    #     return self.session.get(url, headers=self.headers)
#
#     def clear_cart(self):
#         url = "https://download.prosoundeffects.com/ajax.php?p=shopping_cart&action=clear_cart"
#         return self.session.get(url, headers=self.headers)


def is_this_sound_bought_from_sound_dogs(sound_id, username, password):
    auth_session = WebsiteAuth.SoundDogs(username, password)
    if WebsiteAuth.get_order_from_sound_dogs_sound(sound_id, auth_session):
        return True
    return False
