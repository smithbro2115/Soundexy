from Soundexy.Webscraping.Authorization import WebsiteAuth
import requests
from lxml import html
import time

headers = {'Host': 'download.prosoundeffects.com',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0',
			'Accept': '*/*',
			'Accept-Language': 'en-US,en;q=0.5',
			'Accept-Encoding': 'gzip, deflate, br',
			'Referer': 'https://download.prosoundeffects.com/',
			'Content-type': 'application/x-www-form-urlencoded',
			'Connection': 'keep-alive'}
post_data = {'item': {"type": "licensing", "item_id": "17779649-95-0", "track_id": 17779649,
					  "track": {"id": 17779649, "title": "CW002_Moody_Winds_Vast_Dark_Whistling.wav",
								"date": "03/27/2017", "length": "1:33", "actualLength": 93.42933333, "plays": "23,254",
								"downloads": "244", "comments": [], "genres": [{"id": 279196, "name": "Winds"}],
								"tempos": [{"id": 316, "name": "Unspecified"}],
								"cueTypes": [{"id": 195, "name": "Songs"}], "bpm": 0,
								"catalog": {"id": 675, "name": "Pro Sound Effects",
											"image": "https://dm09pscvq9wc9.cloudfront.net/user_data/33375/1415659937-33375-150.png"},
								"label": {"id": 640628, "name": "Pro Sound Effects",
										  "image": "https://dm09pscvq9wc9.cloudfront.net/user_data/33375/1415659937-33375-150.png"},
								"artist": {"id": 390407, "name": "Ann Kroeber, Alan Splet", "description": "",
										   "image": "images/shared/default_artist6.jpg"},
								"composer": {"id": 0, "name": "", "image": "images/shared/default_artist6.jpg"},
								"publisher": {"id": 0, "name": ""}, "writers": [], "publishers": [],
								"album": {"id": 4084354, "name": "Cinematic Winds",
										  "image": "https://dm09pscvq9wc9.cloudfront.net/user_data/117653/1552595751-117653-r.jpg",
										  "code": "", "number": "0"},
								"key": {"id": 0, "name": "Unspecified", "minorId": 0}, "has_vocal": 2, "explicit": 2,
								"isrc": "", "iswc": "", "workNumbers": [], "featured": 17, "userDownloaded": 0,
								"userLastDLdate": 0, "private": 0, "styles": [], "moods": [],
								"description": "Vast Dark Whistling Winds, Deep Howl, Slow Tonal Whistling",
								"keywords": "", "instruments": "", "version": "",
								"formats": {"mp3": 0, "wav": 27043426, "aiff": 0, "extras": [], "disableMp3": 0,
											"disableWav": 0, "disableAiff": 0},
								"file": {"waveform": "https://sourceaudio.s3.amazonaws.com/1/7/7/7/9/6/4/9/17779649.js",
										 "playHtml5": "https://d1ombmsyi1byit.cloudfront.net/1/7/7/7/9/6/4/9/17779649-128.mp3",
										 "waveformCallbackId": 17779649,
										 "filename": "CW002_Moody_Winds_Vast_Dark_Whistling.mp3"}, "custom_fields": [
							  {"id": 17, "name": "Library", "value": "Cinematic Winds", "hidden": 0},
							  {"id": 104, "name": "Designer", "value": "Ann Kroeber, Alan Splet", "hidden": 0},
							  {"id": 359, "name": "Duration", "value": "01:33.4", "hidden": 0}], "can_download": 0,
								"masterId": 17779649, "alternates": [], "alternateCount": 0,
								"alternateDownloadFormats": [], "price": -1, "tagged": 0, "user_projects": [],
								"user_cue_sheets": [], "dateAddedToBank": 1566232353056}, "license": [
		{"title": "Royalty Free", "price": 5,
		 "description": "This license allows you to use this sound in any project, commercial or otherwise.",
		 "key": "0", "agreement": 44}], "project": [], "price": 5, "affiliate": None, "time":1566232364,
					  "index":"1_1566232364"}}

cookies = {'PHPSESSID': '6esc20lvmrqu6jlh3qpo6oabug',
			'sa_user_normal': '111933;$2y$12$nMj7ytTPXWvbx6dua4/r.uKmH6PY6yTWpAnUsMonp9tSGFGHtug7i',
			'sa_user_secure_20151123': '$2y$12$FVgO0M//QGhUIjklbKpmne707tmDQNe1yCZHyLEiOVGceIC.ZUeSS'}

url = "https://download.prosoundeffects.com/ajax.php?p=shopping_cart&action=add_to_cart"
auth_s = WebsiteAuth.ProSound('ian@brinkmanadventures.com', 'David5Grace6pr!')
r = auth_s.session.post(url, json=post_data, headers=headers, cookies=cookies)

print(r, r.content)