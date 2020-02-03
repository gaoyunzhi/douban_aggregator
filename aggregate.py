#!/usr/bin/env python3
# -*- coding: utf-8 -*-

BLACKLIST = ['包邮', '闲鱼', '收藏图书到豆列', '关注了成员:', '恶臭扑鼻', 
'过分傻屌', '傻逼无限']

import requests
from bs4 import BeautifulSoup
from telegram_util import matchKey
import yaml
import hashlib
import sys
import time
import cached_url

try:
	page_limit = int(sys.argv[2])
except:
	page_limit = 20

with open('credential') as f:
    credential = yaml.load(f, Loader=yaml.FullLoader)

def getUrl(url):
	return cached_url.get(url, {'cookie': credential['cookie']})

def hasQuote(item):
	if not item.find('blockquote'):
		return False
	if len(item.find('blockquote').text) < 20:
		return False
	return True

def isBookOrMovie(item):
	return item.find('div', class_='bd book') or item.find('div', class_='bd movie')

def wantSee(item):
	if (not hasQuote(item)) and isBookOrMovie(item):
		return False
	if matchKey(item.text, BLACKLIST):
		return False
	return True

r = None
sids = set()
for page in range(1, page_limit):
	url = 'https://www.douban.com/?p=' + str(page)
	b = BeautifulSoup(getUrl(url), 'html.parser')
	if not r:
		r = BeautifulSoup(getUrl(url), 'html.parser')
		r_center = BeautifulSoup('<div id="wrapper" style="max-width:680px"></div>', features="lxml")
		r.find('div', {'id': 'wrapper'}).replace_with(r_center)
		r.find('div', class_='global-nav').decompose()
		r.find('div', class_='nav').decompose()
	r_center = r.find('div', {'id': 'wrapper'})
	statuses = b.find('div', {'id': 'statuses'})
	for item in statuses.find_all('div', class_='status-item'):
		sid = item.attrs.get('data-sid')
		if sid in sids:
			continue
		sids.add(sid)
		if wantSee(item):
			wr = BeautifulSoup('<div style="padding-bottom:30px"></div>', features="lxml")
			wr.append(item)
			r_center.append(wr)
	for x in r.find_all('div', class_='actions'):
		for y in x.find_all('a', class_='btn'):
			y.decompose()
		for y in x.find_all('span', class_='count'):
			y.decompose()
		for y in x.find_all('a'):
			y.string = '----'
	for x in r.find_all('blockquote'):
		x['style'] = "max-height: 400px; display: block;"
	if page % 5 == 0:
		time.sleep(5)
	with open('result.html', 'w') as f:
		f.write(str(r))