from PyQt5.QtCore import QObject, pyqtSignal
from abc import abstractmethod
from Soundexy.Webscraping.Webscraping import WebScrapers
from Soundexy.Indexing.LocalFileHandler import IndexSearch


class SearchSigs(QObject):
    started = pyqtSignal()
    found_batch = pyqtSignal(list)
    finished = pyqtSignal()


class Search:
    def __init__(self, keywords, excluded_words, thread_pool):
        self.keywords = keywords
        self.signals = SearchSigs()
        self.canceled = False
        self.thread_pool = thread_pool
        self.excluded_words = excluded_words
        self.threads = []

    def run(self):
        pass

    def cancel(self):
        self.canceled = True
        self.cancel_all_threads()

    def emit_batch(self, results):
        if not self.canceled:
            self.signals.found_batch.emit(results)

    def cancel_all_threads(self):
        for thread in self.threads:
            thread.cancel()

    def emit_finished(self):
        if self.thread_pool.activeThreadCount() == 0:
            self.signals.finished.emit()


class RemoteSearch(Search):
    def __init__(self, keywords, excluded_words, thread_pool):
        super(RemoteSearch, self).__init__(keywords, excluded_words, thread_pool)
        self.url = ''
        self.amount_of_pages = 0
        self.start_page = 1

    @property
    @abstractmethod
    def scraper_type(self):
        return WebScrapers.Scraper

    @property
    @abstractmethod
    def page_scraper(self):
        return WebScrapers.PageAmountScraper

    def run(self):
        site = self.page_scraper(self.keywords)
        site.signals.sig_url.connect(self.set_url)
        site.signals.sig_amount_of_pages.connect(self.set_amount_of_pages)
        site.signals.sig_finished.connect(self.scrape)
        self.thread_pool.start(site)

    def scrape(self):
        url = self.url
        amount_of_pages = self.amount_of_pages
        keywords = self.keywords
        page_number = 0
        if amount_of_pages > 0:
            while page_number <= amount_of_pages:
                if self.canceled:
                    break
                search = self.scraper_type(keywords, page_number, url)
                search.signals.sig_results.connect(self.emit_batch)
                search.signals.sig_finished.connect(self.emit_finished)
                self.threads.append(search)
                self.thread_pool.start(search)
                page_number += 1
        else:
            self.emit_finished()

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


class ProSoundSearch(PaidSearch):
    @property
    def scraper_type(self):
        return WebScrapers.ProSoundScraper

    @property
    def page_scraper(self):
        return WebScrapers.ProSoundPageAmountScraper
