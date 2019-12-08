#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import yaml
import hashlib

LIMIT = 2

with open('CREDENTIAL.yaml') as f:
    CREDENTIAL = yaml.load(f, Loader=yaml.FullLoader)

def getUrlContent(url):
	headers = {
		'method': 'GET',
		'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
		'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
		'cookie': CREDENTIAL['cookie'],
	}
	return requests.get(url, headers=headers).text

def _cachedContent(url):
	cache = 'tmp_' + hashlib.sha224(url.encode('utf-8')).hexdigest()[:10] + '.html'
	try:
		with open(cache) as f:
			return f.read()
	except:
		content = getUrlContent(url)
		with open(cache, 'w') as f:
			f.write(content)
		return content

def getUrl(url):
	if 'test' in str(sys.argv):
		content = cachedContent(url)
	else:
		content = getUrlContent(url)

for page in range(1, LIMIT):
	url = 'https://www.douban.com/?p=' + str(page)
	b = BeautifulSoup(getUrl(url), 'html.parser')
	statuses = b.find('div', {'id': 'statuses'})
	for item in statuses.find_all('status-item'):
		print(item.text)