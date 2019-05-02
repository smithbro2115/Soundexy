from Soundexy.Webscraping.Webscraping.WebScraperRequester import simple_get
from bs4 import BeautifulSoup
from math import ceil
from Soundexy.Indexing import SearchResults
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable


# TODO add the rest of the websites

class WebsiteSigs(QObject):
    sig_amount_of_pages = pyqtSignal(int)
    sig_url = pyqtSignal(str)
    sig_finished = pyqtSignal()


class ScraperSigs(QObject):
    sig_results = pyqtSignal(list)
    sig_finished = pyqtSignal()


class Scraper(QRunnable):
    def __init__(self, keywords, page_number, url):
        super(Scraper, self).__init__()
        self.keywords = keywords
        self.signals = ScraperSigs()
        self.page_number = page_number
        self.url = url
        self.canceled = False

    @staticmethod
    def get_results(raw_html):
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
            page_number = self.page_number
            url = self.url
            raw_html = simple_get(url + '&page=' + str(page_number))
            results = []

            raw_results = self.get_results(raw_html)
            for raw_result in raw_results:
                if self.canceled:
                    break
                if raw_result.has_attr('id'):
                    if self.check_attribution(raw_result):
                        result = SearchResults.FreesoundResult()
                        result.preview = 'https://freesound.org' + \
                                         str(raw_result.find('a', {'class': 'ogg_file'}).get('href'))
                        result.set_title(str(raw_result.find('div', {'class': 'sound_filename'})
                                             .find('a', {'class': 'title'}).get('title')))
                        result.duration = ceil(float(raw_result.find('span', {'class': 'duration'}).text))
                        result.description = raw_result.find('div', {'class': 'sound_description'}).find('p').text
                        result.library = 'Freesound'
                        result.author = raw_result.find('a', {'class': 'user'}).text
                        result.link = 'https://freesound.org' + \
                                      str(raw_result.find('div', {'class': 'sound_filename'})
                                          .find('a', {'class': 'title'}).get('href'))
                        result.id = raw_result.get('id')
                        existing_result = result.check_if_already_downloaded()
                        if existing_result:
                            results.append(existing_result)
                        else:
                            results.append(result)

            self.signals.sig_results.emit(results)
        self.signals.sig_finished.emit()


class Website(QRunnable):

    def __init__(self, keywords):
        super(Website, self).__init__()
        self.amount_of_pages = None
        self.keywords = keywords
        self.url = None
        self.amount_of_pages = None
        self.signals = WebsiteSigs()

    def make_url(self):
        return ''

    def get_amount_of_pages(self):
        return int


class Freesound(Website):

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
