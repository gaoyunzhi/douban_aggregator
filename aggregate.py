#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import yaml
import hashlib
import sys

LIMIT = 10

def fact():
	return BeautifulSoup("<div></div>", features="lxml")

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

def cachedContent(url):
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
		return cachedContent(url)
	else:
		return getUrlContent(url)

def hasQuote(item):
	if not item.find('blockquote'):
		return False
	if len(item.find('blockquote').text) < 10:
		return False
	return True

def isBookOrMovie(item):
	return item.find('div', class_='bd book') or item.find('div', class_='bd movie')

def wantSee(item):
	if (not hasQuote(item)) and isBookOrMovie(item):
		return False
	if '关注了成员:' in item.text:
		return False
	return True

r = None
for page in range(1, LIMIT):
	url = 'https://www.douban.com/?p=' + str(page)
	b = BeautifulSoup(getUrl(url), 'html.parser')
	if not r:
		r = BeautifulSoup(getUrl(url), 'html.parser')
		r_center = BeautifulSoup('<div id="wrapper" style="max-width:800px"></div>', features="lxml")
		r.find('div', {'id': 'wrapper'}).replace_with(r_center)
		r.find('div', class_='global-nav').decompose()
		r.find('div', class_='nav').decompose()
	r_center = r.find('div', {'id': 'wrapper'})
	statuses = b.find('div', {'id': 'statuses'})
	for item in statuses.find_all('div', class_='status-item'):
		if wantSee(item):
			wr = BeautifulSoup('<div style="padding-bottom:30px"></div>', features="lxml")
			wr.append(item)
			r_center.append(wr)

for x in r.find_all('div', class_='actions'):
	for y in x.find_all('a', class_='btn'):
		y.decompose()
	for y in x.find_all('a', class_='like-count'):
		y.decompose()

for x in r.find_all('blockquote'):
	x['style'] = "max-height: 400px; display: block;"

r = str(r)
with open('result.html', 'w') as f:
	f.write(r)