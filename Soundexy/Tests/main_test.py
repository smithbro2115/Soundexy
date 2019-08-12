from bs4 import BeautifulSoup
from Soundexy.Webscraping.Webscraping.WebScraperRequester import simple_get
import requests
from lxml import html
import time


register_url = "http://api.sounddogs.com/api/v1/licensing/register"
post_data = {"reqType": 1, 'email': 'brinkmansound@gmail.com', 'licVer': '4699', 'appVer': '1.3.1'}

r = requests.post(register_url, json=post_data)
token = r.json()['token']

print(token)
