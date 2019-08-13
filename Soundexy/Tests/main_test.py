from bs4 import BeautifulSoup
from Soundexy.Webscraping.Webscraping.WebScraperRequester import simple_get
import requests
from lxml import html
import time


register_url = "http://api.sounddogs.com/api/v1/licensing/register"
register_post_data = {"reqType": 1, 'email': 'brinkmansound@gmail.com', 'licVer': '4699', 'appVer': '1.3.1'}

r = requests.post(register_url, json=register_post_data)
token = r.json()['token']

search_url = "http://api.sounddogs.com/api/v1/audioclips"
search_post_data = {'keyword': 'tree', 'pageNumber': 2}
search_headers = {'X-Auth-Token': token}
search_r = requests.post(search_url, json=search_post_data, headers=search_headers)
print(search_r, search_r.json())
