from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5 import QtCore
from abc import abstractmethod
from Soundexy.Functionality.useful_utils import Worker
from Soundexy.Webscraping.Webscraping import WebScrapers
from Soundexy.Webscraping.Authorization.Credentials import get_saved_credentials, delete_saved_credentials
from Soundexy.Webscraping.Authorization.WebsiteAuth import ProSound, LoginError
from Soundexy.Indexing.LocalFileHandler import IndexSearch
from Soundexy.Indexing import SearchResults
from Soundexy.GUI.API.CustomPyQtWidgets import SearchCheckBoxContextMenu, make_standard_items_from_results, \
    SearchResultsItemModel
import time
import re
import traceback
import shlex


class SearchHandler:
    def __init__(self, parent):
        self.parent = parent
        self.search_line_text = None
        self.running_search_keywords = []
        self.local_search = None
        self.running_libraries = []
        self.running_processor = SearchHitProcessor(self.parent.searchResultsTable.current_results, self.parent)
        self.running_processor.signals.batch_done.connect(self.parent.searchResultsTable.switch_model)
        self.running_searches = {}
        self.local_search_thread_pool = QtCore.QThreadPool()
        self.processor_thread_pool = QtCore.QThreadPool()
        self.remote_search_thread_pool = QtCore.QThreadPool()
        self.local_search_thread_pool.setMaxThreadCount(2)
        self.remote_search_thread_pool.setMaxThreadCount(4)
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
        contexts = self.get_all_checked_context_menus()
        libraries += self.get_all_checked_libraries(*contexts)
        return libraries

    def start_search(self):
        self.search_line_text = re.escape(self.parent.searchLineEdit.text())
        if not self.search_line_text.strip() == '':
            keywords, excluded_words, required_keywords, unnecessary_keywords = self.get_keywords()
            if self.running_search_keywords != keywords or self.running_libraries != self.checked_search_libraries:
                self.run_search(keywords, excluded_words)
        else:
            self.reset_searches()
            self.running_search_keywords = []

    def run_search(self, keywords,  excluded_words):
        self.reset_searches()
        self.clear_found_label()
        self.parent.start_busy_indicator_search()
        local = self.search_state_local
        self.running_libraries = self.checked_search_libraries
        self.running_search_keywords = keywords
        if local:
            self.run_local_search(self.search_line_text)
        self.run_remote_search(keywords, excluded_words)
        if len(self.running_searches) <= 0:
            self.finished_search(None)

    def add_to_running_searches(self, search):
        index = f"search_{len(self.running_searches.keys())}"
        self.running_searches[index] = search
        return index

    def run_local_search(self, search_text):
        sort_column = self.parent.searchResultsTable.model().columns[
            self.parent.searchResultsTable.horizontalHeader().sortIndicatorSection()]
        search = IndexSearch(search_text, sort_by=sort_column)
        index = self.add_to_running_searches(search)
        search.signals.batch_found.connect(self.add_hits_to_search_results_table)
        search.signals.finished.connect(lambda: self.finished_search(index))
        self.local_search_thread_pool.start(search)

    def add_hits_to_search_results_table(self, hits):
        self.make_results_from_hits_in_thread(hits)

    def make_results_from_hits_in_thread(self, hits):
        try:
            self.running_processor.add_to_local_queue(hits)
        except ProcessorCanceled:
            self.running_processor = SearchHitProcessor(self.parent.searchResultsTable.current_results, self.parent)
            self.running_processor.signals.batch_done.connect(self.parent.searchResultsTable.switch_model)
            self.make_results_from_hits_in_thread(hits)
        if self.processor_thread_pool.activeThreadCount() == 0:
            self.processor_thread_pool.start(self.running_processor)

    def add_to_processor_remote_queue(self, results):
        try:
            self.running_processor.add_to_remote_queue(results)
        except ProcessorCanceled:
            self.running_processor = SearchHitProcessor(self.parent.searchResultsTable.current_results, self.parent)
            self.running_processor.signals.batch_done.connect(self.parent.searchResultsTable.switch_model)
            self.add_to_processor_remote_queue(results)
        if self.processor_thread_pool.activeThreadCount() == 0:
            self.processor_thread_pool.start(self.running_processor)

    def run_remote_search(self, keywords, excluded_words):
        actions = self.get_all_checked_actions(*self.get_all_checked_context_menus())
        for action in actions:
            search = action.data()(keywords, excluded_words, self.remote_search_thread_pool)
            index = self.add_to_running_searches(search)
            search.signals.found_batch.connect(self.add_to_processor_remote_queue)
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

    @staticmethod
    def clear_search_results_table(table, current_results):
        current_results.clear()
        table.go_to_empty_model()

    def reset_searches(self):
        # worker = Worker(self.clear_search_results_table,
        #                 self.parent.searchResultsTable,
        #                 self.parent.searchResultsTable.current_results)
        # self.processor_thread_pool.start(worker)
        # current_results.clear()
        self.cancel_all_running_searches()
        self.parent.searchResultsTable.go_to_empty_model()
        self.parent.clear_cache_in_separate_thread()

    def cancel_all_running_searches(self):
        self.running_processor.canceled = True
        try:
            self.cancel_searches(self.running_searches)
        except RuntimeError:
            self.cancel_all_running_searches()

    @staticmethod
    def cancel_searches(searches):
        for search in searches.values():
            search.cancel()

    def clear_found_label(self):
        self.parent.messageLabel.setText("")

    def finished_search(self, search_index):
        if search_index:
            del self.running_searches[search_index]
        if len(self.running_searches) <= 0:
            self.parent.stop__busy_indicator_search()
            self.running_processor.search_done = True


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
        self.pages_done = 0
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
        self.url = url

    def set_amount_of_pages(self, amount):
        self.amount_of_pages = amount

    def emit_finished(self):
        self.pages_done += 1
        if self.amount_of_pages <= self.pages_done:
            self.signals.finished.emit(self.index)
            self.running = False


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
    def __init__(self, keywords, excluded_words, thread_pool, sort_by):
        super(LocalSearch, self).__init__(keywords, excluded_words, thread_pool)
        self.excluded_words = excluded_words
        self.sort_by = sort_by

    def run(self, index):
        self.index = index
        search = IndexSearch(self.keywords, self.excluded_words, sort_by=self.sort_by)
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


class ProcessorCanceled(Exception):
    pass


class SearchHitProcessorSignals(QObject):
    batch_done = pyqtSignal(SearchResultsItemModel)
    finished = pyqtSignal()


class SearchHitProcessor(QtCore.QRunnable):
    def __init__(self, current_results, parent):
        super(SearchHitProcessor, self).__init__()
        self.signals = SearchHitProcessorSignals()
        self.local_queue = []
        self.remote_queue = []
        self.counter = 0
        self.canceled = False
        self.search_done = False
        self.parent = parent
        self.model = SearchResultsItemModel([], parent.searchResultsTable)
        self.sort_model = QtCore.QSortFilterProxyModel()
        self.sort_model.setSourceModel(self.model)
        parent.searchResultsTable.setModel(self.sort_model)
        self.current_results = current_results

    @property
    def next_in_local_queue(self):
        try:
            return self.local_queue.pop(0)
        except IndexError:
            return []

    @property
    def next_in_remote_queue(self):
        try:
            return self.remote_queue.pop(0)
        except IndexError:
            return []

    def cancel(self):
        self.canceled = True

    def add_to_local_queue(self, hits):
        if self.canceled:
            raise ProcessorCanceled
        else:
            self.local_queue.append(hits)

    def add_to_remote_queue(self, results):
        if self.canceled:
            raise ProcessorCanceled
        else:
            try:
                if len(self.remote_queue[-1]) < 50:
                    self.remote_queue[-1] += results
                else:
                    self.remote_queue.append(results)
            except IndexError:
                self.remote_queue.append(results)

    @pyqtSlot()
    def run(self):
        while not self.canceled:
            self.run_local()
            self.run_remote()
            time.sleep(.1)

    def run_local(self):
        hits = self.next_in_local_queue
        if len(hits) > 0:
            results = self.make_results_from_hits(hits)
            if not self.canceled:
                self.add_to_model(results)

    def run_remote(self):
        try:
            if len(self.remote_queue[0]) >= 50 or self.search_done:
                if not self.canceled:
                    self.add_to_model(self.next_in_remote_queue)
        except IndexError:
            pass

    def add_to_model(self, results):
        self.model.insertRows(self.model.rowCount(), len(results), rows=results)
        self.parent.searchResultsTable.update_found_label()

    @staticmethod
    def make_results_from_hits(hits):
        results = []
        for hit in hits:
            try:
                results.append(SearchResults.Local(hit))
            except KeyError:
                pass
        return results
