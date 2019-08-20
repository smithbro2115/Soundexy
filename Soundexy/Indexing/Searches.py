from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5 import QtCore
from abc import abstractmethod
from Soundexy.Functionality.useful_utils import Worker
from Soundexy.Webscraping.Webscraping import WebScrapers
from Soundexy.Webscraping.Authorization.Credentials import get_saved_credentials, delete_saved_credentials
from Soundexy.Webscraping.Authorization.WebsiteAuth import ProSound, LoginError
from Soundexy.Indexing.LocalFileHandler import IndexSearch
from Soundexy.GUI.API.CustomPyQtWidgets import SearchCheckBoxContextMenu
import traceback
import re
import shlex


class SearchHandler:
    def __init__(self, parent):
        self.parent = parent
        self.search_line_text = None
        self.running_search_keywords = []
        self.local_search = None
        self.running_libraries = []
        self.running_searches = {}
        self.local_search_thread_pool = QtCore.QThreadPool()
        self.remote_search_thread_pool = QtCore.QThreadPool()
        self.local_search_thread_pool.setMaxThreadCount(1)
        self.freeSearchCheckboxContext = None
        self.paidSearchCheckboxContext = None

    def setup(self):
        self.freeSearchCheckboxContext = SearchCheckBoxContextMenu(FreeSearch.__subclasses__(),
                                                                   self.parent.topbarLibraryFreeCheckbox)
        self.paidSearchCheckboxContext = SearchCheckBoxContextMenu(PaidSearch.__subclasses__(),
                                                                   self.parent.topbarLibraryPaidCheckbox)
        self.parent.topbarLibraryFreeCheckbox.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.parent.topbarLibraryFreeCheckbox.customContextMenuRequested.connect(self.free_checkbox_right_clicked)
        self.parent.topbarLibraryPaidCheckbox.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.parent.topbarLibraryPaidCheckbox.customContextMenuRequested.connect(self.paid_search_right_clicked)

    def free_checkbox_right_clicked(self, event):
        self.freeSearchCheckboxContext.exec_(self.parent.topbarLibraryFreeCheckbox.mapToGlobal(event))

    def paid_search_right_clicked(self, event):
        self.paidSearchCheckboxContext.exec_(self.parent.topbarLibraryPaidCheckbox.mapToGlobal(event))

    @property
    def search_state_local(self):
        return self.parent.topbarLibraryLocalCheckbox.checkState()

    @property
    def search_state_free(self):
        return self.parent.topbarLibraryFreeCheckbox.checkState()

    @property
    def search_state_paid(self):
        return self.parent.topbarLibraryPaidCheckbox.checkState()

    @property
    def checked_search_libraries(self):
        libraries = []
        if self.search_state_local:
            libraries.append(self.parent.topbarLibraryLocalCheckbox.text())
        libraries += self.get_all_checked_libraries(self.freeSearchCheckboxContext,
                                                    self.paidSearchCheckboxContext)
        return libraries

    def start_search(self):
        self.search_line_text = self.parent.searchLineEdit.text()
        if not self.search_line_text.strip() == '':
            keywords, excluded_words, required_keywords, unnecessary_keywords = self.get_keywords()
            if self.running_search_keywords != keywords or self.running_libraries != self.checked_search_libraries:
                self.run_search(keywords, required_keywords, unnecessary_keywords, excluded_words)
        else:
            self.reset_searches()
            self.running_search_keywords = []

    def run_search(self, keywords, required_keywords, unnecessary_keywords, excluded_words):
        self.reset_searches()
        self.parent.start_busy_indicator_search()
        local = self.search_state_local
        self.running_libraries = self.checked_search_libraries
        self.running_search_keywords = keywords
        if local:
            self.run_local_search(required_keywords, unnecessary_keywords, excluded_words)
        self.run_remote_search(keywords, excluded_words)
        if len(self.running_searches) <= 0:
            self.finished_search(None)

    def add_to_running_searches(self, search):
        index = f"search_{len(self.running_searches.keys())}"
        self.running_searches[index] = search
        return index

    def run_local_search(self, required_keywords, unnecessary_keywords, excluded_words):
        search = IndexSearch(unnecessary_keywords, required_keywords, excluded_words)
        index = self.add_to_running_searches(search)
        search.signals.batch_found.connect(self.parent.searchResultsTable.add_results_to_search_results_table)
        search.signals.finished.connect(lambda: self.finished_search(index))
        self.local_search_thread_pool.start(search)

    def run_remote_search(self, keywords, excluded_words):
        actions = self.get_all_checked_actions(*self.get_all_checked_context_menus())
        for action in actions:
            search = action.data()(keywords, excluded_words, self.remote_search_thread_pool)
            index = self.add_to_running_searches(search)
            search.signals.found_batch.connect(self.parent.searchResultsTable.add_results_to_search_results_table)
            search.signals.finished.connect(self.finished_search)
            search.signals.canceled.connect(self.finished_search)
            search.run(index)

    @staticmethod
    def get_excluded_keywords(keywords):
        excluded_words = []
        for keyword in keywords:
            if keyword.startswith('-'):
                excluded_words.append(keyword[1:])
                keywords.remove(keyword)
        return excluded_words, keywords

    @staticmethod
    def get_required_and_unnecessary_keywords(keywords):
        required_keywords = []
        unnecessary_keywords = []
        for keyword in keywords:
            sub_keywords = keyword.split()
            if len(sub_keywords) > 1:
                required_keywords += sub_keywords
            else:
                unnecessary_keywords.append(keyword)
        return required_keywords, unnecessary_keywords

    def get_keywords(self):
        remote_keywords = re.sub('[^\w-]', ' ', self.search_line_text).lower().split()
        keywords = shlex.split(self.search_line_text.lower())
        excluded_keywords, keywords = self.get_excluded_keywords(keywords)
        required_keywords, unnecessary_keywords = self.get_required_and_unnecessary_keywords(keywords)
        return remote_keywords, excluded_keywords, required_keywords, unnecessary_keywords


    @staticmethod
    def get_all_checked_actions(*checkbox_contexts):
        checked_actions = []
        for checkbox_context in checkbox_contexts:
            for action in checkbox_context.actions():
                if action.isChecked():
                    checked_actions.append(action)
        return checked_actions

    def get_all_checked_context_menus(self):
        menus = []
        if self.search_state_free:
            menus.append(self.freeSearchCheckboxContext)
        if self.search_state_paid:
            menus.append(self.paidSearchCheckboxContext)
        return menus

    def get_all_checked_libraries(self, *checkbox_contexts):
        libraries = []
        actions = self.get_all_checked_actions(*checkbox_contexts)
        for action in actions:
            libraries.append(action.text())
        return libraries

    def clear_search_results_table(self):
        self.parent.searchResultsTable.searchResultsTableModel.setRowCount(0)
        self.parent.searchResultsTable.current_results = {}

    def reset_searches(self):
        self.clear_search_results_table()
        self.parent.clear_cache_in_separate_thread()
        self.cancel_all_running_searches()

    def cancel_all_running_searches(self):
        self.cancel_searches(self.running_searches)

    @staticmethod
    def cancel_searches(searches):
        for search in searches:
            search.cancel()

    def finished_search(self, search_index):
        del self.running_searches[search_index]
        if len(self.running_searches) <= 0:
            self.parent.stop__busy_indicator_search()


class SearchSigs(QObject):
    started = pyqtSignal()
    found_batch = pyqtSignal(list)
    canceled = pyqtSignal(str)
    finished = pyqtSignal(str)


class Search:
    def __init__(self, keywords, excluded_words, thread_pool):
        self.keywords = keywords
        self.index = None
        self.signals = SearchSigs()
        self.canceled = False
        self.thread_pool = thread_pool
        self.excluded_words = excluded_words
        self.threads = []
        self.running = True

    def run(self, index):
        pass

    def cancel(self):
        self.canceled = True
        self.cancel_all_threads()
        self.running = False
        self.signals.canceled.emit(self.index)

    def emit_batch(self, results):
        if not self.canceled:
            self.signals.found_batch.emit(results)

    def cancel_all_threads(self):
        for thread in self.threads:
            thread.cancel()

    def emit_finished(self):
        self.signals.finished.emit(self.index)
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

    def run(self, index):
        try:
            self.index = index
            site = self.page_scraper(self.keywords)
            site.signals.sig_url.connect(self.set_url)
            site.signals.sig_amount_of_pages.connect(self.set_amount_of_pages)
            site.signals.sig_finished.connect(self.scrape)
            self.thread_pool.start(site)
        except:
            traceback.print_exc()
            self.canceled = True
            self.signals.canceled.emit(self.index)

    def scrape(self):
        try:
            url = self.url
            amount_of_pages = self.amount_of_pages
            keywords = self.keywords
            page_number = self.start_page
            if amount_of_pages > 0:
                while page_number <= amount_of_pages:
                    if self.canceled:
                        self.signals.canceled.emit(self.index)
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
            self.signals.canceled.emit(self.index)

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

    def run(self, index):
        self.index = index
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
            print('pro sound login error')
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
