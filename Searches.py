from PyQt5.QtCore import QRunnable, QObject, pyqtSignal, pyqtSlot
import abc
import WebScrapers


class SearchSigs(QObject):
    started = pyqtSignal()
    found_batch = pyqtSignal(list)
    finished = pyqtSignal()


class Search:
    def __init__(self, keywords, thread_pool):
        self.keywords = keywords
        self.signals = SearchSigs()
        self.canceled = False
        self.thread_pool = thread_pool
        self.url = ''
        self.amount_of_pages = 0
        self.threads = []

    def cancel(self):
        self.canceled = True

    @abc.abstractmethod
    def run(self):
        pass

    def emit_batch(self, results):
        if not self.canceled:
            self.signals.found_batch.emit(results)

    def emit_finished(self):
        self.signals.finished.emit()


class FreesoundSearch(Search):
    def __init__(self, keywords, thread_pool):
        super(FreesoundSearch, self).__init__(keywords, thread_pool)

    def run(self):
        freesound_site = WebScrapers.Freesound(self.keywords)
        freesound_site.signals.sig_url.connect(self.set_url)
        freesound_site.signals.sig_amount_of_pages.connect(self.freesound_set_amount_of_pages)
        freesound_site.signals.sig_finished.connect(self.scrape)
        self.thread_pool.start(freesound_site)

    def set_url(self, url):
        self.url = url

    def freesound_set_amount_of_pages(self, amount):
        self.amount_of_pages = amount

    def scrape(self):
        url = self.url
        amount_of_pages = self.amount_of_pages
        keywords = self.keywords
        page_number = 0
        if amount_of_pages > 0:
            while page_number < amount_of_pages:
                if self.canceled:
                    break
                page_number += 1
                free_search = WebScrapers.FreesoundScraper(keywords, page_number, url)
                free_search.signals.sig_results.connect(self.emit_batch)
                free_search.signals.sig_finished.connect(self.emit_finished)
                self.threads.append(free_search)
                self.thread_pool.start(free_search)
        else:
            self.emit_finished()

    def cancel(self):
        super(FreesoundSearch, self).cancel()
        self.cancel_all_threads()

    def cancel_all_threads(self):
        for thread in self.threads:
            thread.cancel()
