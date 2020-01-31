from Soundexy.Webscraping.Webscraping.WebScraperRequester import simple_get, get_with_headers
from bs4 import BeautifulSoup
from lxml import html as lxml_html
from math import ceil
from Soundexy.Indexing import SearchResults
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable, QThreadPool


# TODO add the rest of the websites


class TestObject:
    pass


class WebsiteSigs(QObject):
    sig_amount_of_pages = pyqtSignal(int)
    sig_url = pyqtSignal(str)
    sig_finished = pyqtSignal()


class ScraperSigs(QObject):
    sig_results = pyqtSignal(list)
    sig_finished = pyqtSignal()


class Scraper(QRunnable):
    def __init__(self, keywords, page_number, url, session=None):
        super(Scraper, self).__init__()
        self.session = session
        self.keywords = keywords
        self.signals = ScraperSigs()
        self.page_number = page_number
        self.url = url
        self.canceled = False

    @staticmethod
    def get_results(raw_html):
        pass

    def make_result_from_raw(self, raw_result):
        pass

    def cancel(self):
        self.canceled = True


class FreesoundScraper(Scraper):
    @staticmethod
    def get_results(raw_html):
        try:
            html = BeautifulSoup(raw_html, 'html.parser')
            return html.find_all('div', {'class': 'sample_player_small'})
        except Exception:
            print("Something didn't work!")

    @staticmethod
    def check_attribution(result):
        attribution = str(result.find('img', {'class': 'cc_license'}).get('alt'))
        if attribution == 'Creative Commons Attribution license' or attribution == 'Public Domain license':
            return True
        else:
            return False

    @pyqtSlot()
    def run(self):
        if not self.canceled:
            raw_html = simple_get(self.url + '&page=' + str(self.page_number))
            results = []
            for raw_result in self.get_results(raw_html):
                if self.canceled:
                    break
                if raw_result.has_attr('id'):
                    if self.check_attribution(raw_result):
                        result = self.make_result_from_raw(raw_result)
                        existing_result = result.check_if_already_downloaded()
                        if existing_result:
                            results.append(existing_result)
                        else:
                            results.append(result)
            self.signals.sig_results.emit(results)
        self.signals.sig_finished.emit()

    def make_result_from_raw(self, raw_result):
        result = SearchResults.FreesoundResult()
        result.meta_file["preview_link"] = 'https://freesound.org' + \
                                           str(raw_result.find('a', {'class': 'ogg_file'}).get('href'))
        result.set_title(str(raw_result.find('div', {'class': 'sound_filename'})
                             .find('a', {'class': 'title'}).get('title')))
        result.file_name = result.title
        result.meta_file["duration"] = ceil(float(raw_result.find('span', {'class': 'duration'}).text))
        result.meta_file["description"] = raw_result.find('div', {'class': 'sound_description'}).find('p').text
        result.meta_file["library"] = 'Freesound'
        result.meta_file["author"] = raw_result.find('a', {'class': 'user'}).text
        result.meta_file["download_link"] = 'https://freesound.org' + \
                               str(raw_result.find('div', {'class': 'sound_filename'})
                                   .find('a', {'class': 'title'}).get('href'))
        result.meta_file["original_id"] = raw_result.get('id')
        result.meta_file["id"] = 'freesound_' + str(result.original_id)
        return result


class SoundDogsScraper(Scraper):
    @staticmethod
    def get_results(raw_html):
        try:
            root = lxml_html.fromstring(raw_html)
            table = root.xpath('//table[@id="searchResultsTable"]')
            return table[0].xpath('//tbody/tr')
        except Exception as e:
            print("Something didn't work!  " + str(e))

    @pyqtSlot()
    def run(self):
        if not self.canceled:
            raw_html = simple_get(self.url + '&page=' + str(self.page_number))
            results = []
            for raw_result in self.get_results(raw_html):
                if self.canceled:
                    break
                result = self.make_result_from_raw(raw_result)
                existing_result = result.check_if_already_downloaded()
                if existing_result:
                    results.append(existing_result)
                else:
                    results.append(result)
            self.signals.sig_results.emit(results)
        self.signals.sig_finished.emit()

    def make_result_from_raw(self, raw_result):
        result = SearchResults.SoundDogsResult()
        result.meta_file["preview_link"] = 'https://sounddogs.com' + \
                         str(raw_result.xpath("td[contains(@class, 'preview')]/a")[0].get('href'))
        result.meta_file["duration"] = ceil(float(raw_result.xpath("td[contains(@class, 'duration')]/text()")[0].strip()
                                     .replace(',', ''))*1000)
        result.meta_file["description"] = raw_result.xpath("td[contains(@class, 'description')]/a")[0].text.strip()
        result.set_title(result.description)
        result.meta_file["file_name"] = result.title
        result.meta_file["channels"] = raw_result.xpath("td[contains(@class, 'channels')]")[0].text.strip()
        result.meta_file["library"] = 'Sounddogs'
        result.meta_file["price"] = int(float(raw_result.xpath("th[contains(@class, 'price')]/span")[0].text.strip().replace('$', '')
                                 )*100)
        result.meta_file["download_link"] = 'https://sounddogs.com' + \
                      str(raw_result.xpath("td[contains(@class, 'description')]/a")[1].get('href'))
        result.meta_file["original_id"] = (str(raw_result.get('id').strip().replace("currentMediaTr_", "")))
        result.meta_file["id"] = 'sounddogs_' + str(result.original_id)
        return result


class ProSoundScraper(Scraper):
    @staticmethod
    def get_results(json):
        raw_results = []
        for raw_result in json['content']:
            if 'id' in raw_result.keys():
                raw_results.append(raw_result)
        return raw_results

    @pyqtSlot()
    def run(self):
        if not self.canceled:
            raw_json = get_with_headers(self.url + '&pg=' + str(self.page_number), self.session).json()
            results = []
            for raw_result in self.get_results(raw_json):
                if self.canceled:
                    break
                result = self.make_result_from_raw(raw_result)
                existing_result = result.check_if_already_downloaded()
                if existing_result:
                    results.append(existing_result)
                else:
                    results.append(result)
            self.signals.sig_results.emit(results)
        self.signals.sig_finished.emit()

    def make_result_from_raw(self, raw_result):
        result = SearchResults.ProSoundResult()
        result.meta_file["preview_link"] = raw_result['file']['playHtml5']
        result.set_title(raw_result['title'])
        result.meta_file["file_name"] = raw_result['title']
        result.meta_file["duration"] = ceil(float(raw_result['actualLength'])*1000)
        result.meta_file["description"] = raw_result['description']
        result.meta_file["library"] = 'Pro Sound'
        result.meta_file["file_type"] = 'wav'
        result.meta_file["author"] = raw_result['artist']['name']
        result.meta_file["download_link"] = raw_result['file']['waveform']
        result.meta_file["original_id"] = raw_result['id']
        result.meta_file["price"] = int(raw_result['price'])
        result.meta_file["bought"] = bool(raw_result['can_download'])
        result.meta_file["id"] = 'prosound_' + str(raw_result['id'])
        return result


class PageAmountScraper(QRunnable):

    def __init__(self, keywords):
        super(PageAmountScraper, self).__init__()
        self.amount_of_pages = None
        self.keywords = keywords
        self.url = None
        self.amount_of_pages = None
        self.signals = WebsiteSigs()

    def make_url(self):
        return ''

    def get_amount_of_pages(self):
        return int


class FreesoundPageAmountScraper(PageAmountScraper):
    def make_url(self):
        url = 'https://freesound.org/search/?q='
        for keyword in self.keywords:
            url = url + '+' + keyword
        return url + '&f=duration%3A%5B0+TO+*%5D&s=num_downloads+desc&advanced=1&g='

    def get_amount_of_pages(self):
        raw_html = simple_get(self.url)
        html = BeautifulSoup(raw_html, 'html.parser')
        try:
            number_of_results_raw =\
                html.find('div', {'class': 'search_paginator'}).find('p', {'class': 'number_of_results'}).text.strip()
        except AttributeError:
            return 0
        number_of_results_string = ''
        for s in number_of_results_raw.split():
            if s.isdigit():
                number_of_results_string = number_of_results_string + s
        number_of_results = int(number_of_results_string)
        return ceil(number_of_results/15)

    @pyqtSlot()
    def run(self):
        self.url = self.make_url()
        self.amount_of_pages = self.get_amount_of_pages()
        self.signals.sig_amount_of_pages.emit(self.amount_of_pages)
        self.signals.sig_url.emit(self.url)
        self.signals.sig_finished.emit()


class ProSoundPageAmountScraper(PageAmountScraper):
    @property
    def ajax_nonce_key(self):
        pass

    def make_url(self):
        url = 'https://download.prosoundeffects.com/ajax.php?p=track_info&show=30&s='
        for keyword in self.keywords:
            url = url + '+' + keyword
        return url

    def get_amount_of_pages(self):
        json = get_with_headers(self.url).json()
        print(json)
        return ceil(json['content'][0]['facets']['tracks']/30)

    @pyqtSlot()
    def run(self):
        self.url = self.make_url()
        self.amount_of_pages = self.get_amount_of_pages()
        self.signals.sig_amount_of_pages.emit(self.amount_of_pages)
        self.signals.sig_url.emit(self.url)
        self.signals.sig_finished.emit()


class SoundDogsPageAmountScraper(PageAmountScraper):
    def make_url(self):
        url = 'https://sounddogs.com/search?keywords='
        for index, keyword in enumerate(self.keywords):
            if index > 0:
                url = url + '+' + keyword
            else:
                url = url + keyword
        return url

    def get_amount_of_pages(self):
        raw_html = simple_get(self.url)
        root = lxml_html.fromstring(raw_html)
        return ceil(int(root.xpath('//span[@class="quantity"]/text()')[0].replace(',', ''))/30)

    @pyqtSlot()
    def run(self):
        self.url = self.make_url()
        self.amount_of_pages = self.get_amount_of_pages()
        self.signals.sig_amount_of_pages.emit(self.amount_of_pages)
        self.signals.sig_url.emit(self.url)
        self.signals.sig_finished.emit()


raw_html = get_with_headers("https://download.prosoundeffects.com/").content
tree = lxml_html.fromstring(raw_html)
script_tags = tree.xpath('//head/script')
print(script_tags)

# thread_pool = QThreadPool()
# scraper = SoundDogsPageAmountScraper(['gobblygooo'])
# scraper.signals.sig_amount_of_pages.connect(print)
# thread_pool.start(scraper)
#
# import time
# while thread_pool.activeThreadCount() > 0:
#     time.sleep(.5)
