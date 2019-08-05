from bs4 import BeautifulSoup, SoupStrainer
from Soundexy.Webscraping.Webscraping.WebScraperRequester import simple_get
from lxml import html
import time


def get_results(raw_html):
	try:
		print('first')
		strainer = SoupStrainer('table', attrs={'id': 'searchResultsTable'})
		html = BeautifulSoup(raw_html, 'lxml', parse_only=strainer)
		table = html.find_all('table', {'id': 'searchResultsTable'})
		return table[0].find('tbody').find_all('tr')
	except Exception as e:
		print("Something didn't work!  " + str(e))


url = "https://www.sounddogs.com/search?keywords=humvee"
raw_html = simple_get(url)
print('lxml start')
start = time.time()
processed = html.fromstring(raw_html)
table = processed.xpath('//table[@id="searchResultsTable"]')
print(html.tostring(table[0]))
print('lxml stop, total time: ' + str(time.time() - start))
