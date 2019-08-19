from PyQt5.QtCore import QObject, pyqtSignal
from abc import abstractmethod
from Soundexy.Functionality.useful_utils import Worker
from Soundexy.Webscraping.Webscraping import WebScrapers
from Soundexy.Webscraping.Authorization.Credentials import get_saved_credentials, delete_saved_credentials
from Soundexy.Webscraping.Authorization.WebsiteAuth import ProSound, LoginError
from Soundexy.Indexing.LocalFileHandler import IndexSearch
import traceback


class SearchSigs(QObject):
    started = pyqtSignal()
    found_batch = pyqtSignal(list)
    canceled = pyqtSignal()
    finished = pyqtSignal()


class Search:
    def __init__(self, keywords, excluded_words, thread_pool):
        self.keywords = keywords
        self.signals = SearchSigs()
        self.canceled = False
        self.thread_pool = thread_pool
        self.excluded_words = excluded_words
        self.threads = []
        self.running = True

    def run(self):
        pass

    def cancel(self):
        self.canceled = True
        self.cancel_all_threads()
        self.running = False
        self.signals.canceled.emit()

    def emit_batch(self, results):
        if not self.canceled:
            self.signals.found_batch.emit(results)

    def cancel_all_threads(self):
        for thread in self.threads:
            thread.cancel()

    def emit_finished(self):
        if self.thread_pool.activeThreadCount() == 0:
            self.signals.finished.emit()
            self.running = False


class RemoteSearch(Search):
    def __init__(self, keywords, excluded_words, thread_pool):
        super(RemoteSearch, self).__init__(keywords, excluded_words, thread_pool)
        self.url = ''
        self.amount_of_pages = 0
        self.start_page = 1
        self.session = None

    @property
    @abstractmethod
    def scraper_type(self):
        return WebScrapers.Scraper

    @property
    @abstractmethod
    def page_scraper(self):
        return WebScrapers.PageAmountScraper

    def run(self):
        try:
            site = self.page_scraper(self.keywords)
            site.signals.sig_url.connect(self.set_url)
            site.signals.sig_amount_of_pages.connect(self.set_amount_of_pages)
            site.signals.sig_finished.connect(self.scrape)
            self.thread_pool.start(site)
        except:
            traceback.print_exc()
            self.canceled = True
            self.signals.canceled.emit()

    def scrape(self):
        try:
            url = self.url
            amount_of_pages = self.amount_of_pages
            keywords = self.keywords
            page_number = self.start_page
            if amount_of_pages > 0:
                while page_number <= amount_of_pages:
                    if self.canceled:
                        break
                    search = self.scraper_type(keywords, page_number, url, session=self.session)
                    search.signals.sig_results.connect(self.emit_batch)
                    search.signals.sig_finished.connect(self.emit_finished)
                    self.threads.append(search)
                    self.thread_pool.start(search)
                    page_number += 1
            else:
                self.emit_finished()
        except:
            traceback.print_exc()
            self.canceled = True
            self.signals.canceled.emit()

    def set_url(self, url):
        self.url = url

    def set_amount_of_pages(self, amount):
        self.amount_of_pages = amount


class FreeSearch(RemoteSearch):
    @property
    def scraper_type(self):
        return WebScrapers.Scraper

    @property
    def page_scraper(self):
        return WebScrapers.PageAmountScraper


class PaidSearch(RemoteSearch):
    def __init__(self, keywords, excluded_words, thread_pool):
        super(PaidSearch, self).__init__(keywords, excluded_words, thread_pool)
        self.start_page = 0

    @property
    def scraper_type(self):
        return WebScrapers.Scraper

    @property
    def page_scraper(self):
        return WebScrapers.PageAmountScraper


class LocalSearch(Search):
    def __init__(self, keywords, excluded_words, thread_pool):
        super(LocalSearch, self).__init__(keywords, excluded_words, thread_pool)
        self.excluded_words = excluded_words

    def run(self):
        search = IndexSearch(self.keywords, self.excluded_words)
        search.signals.batch_found.connect(self.emit_batch)
        search.signals.finished.connect(self.emit_finished)
        self.thread_pool.start(search)


class DefaultLocalSearch(LocalSearch):
    pass


class FreesoundSearch(FreeSearch):
    @property
    def scraper_type(self):
        return WebScrapers.FreesoundScraper

    @property
    def page_scraper(self):
        return WebScrapers.FreesoundPageAmountScraper


class SoundDogsSearch(PaidSearch):
    def __init__(self, keywords, excluded_words, thread_pool):
        super(SoundDogsSearch, self).__init__(keywords, excluded_words, thread_pool)
        self.start_page = 1

    @property
    def scraper_type(self):
        return WebScrapers.SoundDogsScraper

    @property
    def page_scraper(self):
        return WebScrapers.SoundDogsPageAmountScraper


class ProSoundSearch(PaidSearch):
    def set_session(self, session):
        self.session = session
        super(ProSoundSearch, self).scrape()

    def scrape(self):
        try:
            credentials = get_saved_credentials('Pro Sound')
            worker = Worker(ProSound, *credentials)
            worker.signals.result.connect(self.set_session)
            worker.signals.error.connect(self.search_login_error)
            self.thread_pool.start(worker)
        except (KeyError, LoginError):
            super(ProSoundSearch, self).scrape()

    def search_login_error(self, exception):
        if exception[0] == LoginError:
            delete_saved_credentials('Pro Sound')
            super(ProSoundSearch, self).scrape()


    @property
    def scraper_type(self):
        return WebScrapers.ProSoundScraper

    @property
    def page_scraper(self):
        return WebScrapers.ProSoundPageAmountScraper
