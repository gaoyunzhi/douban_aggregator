#!/usr/bin/env python3
# -*- coding: utf-8 -*-

BLACKLIST = ['包邮', '闲鱼', '收藏图书到豆列', '关注了成员:', '恶臭扑鼻', 
'过分傻屌', '傻逼无限', '淘宝店']

from bs4 import BeautifulSoup
from telegram_util import matchKey
import yaml
import sys
import cached_url
from telegram.ext import Updater, MessageHandler, Filters
from telegram import InputMediaPhoto
from telegram_util import log_on_fail
import urllib.request
from PIL import Image

try:
	page_limit = int(sys.argv[1])
except:
	page_limit = 20

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)

tele = Updater(credential['bot_token'], use_context=True)
debug_group = tele.bot.get_chat(-1001198682178)
douban_channel = tele.bot.get_chat(-1001206770471)

with open('existing') as f:
	existing = yaml.load(f, Loader=yaml.FullLoader)

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

def dataCount(item):
	for x in item.find_all('span', class_='count'):
		r = int(x.get('data-count'))
		if r:
			yield r

def wantSee(item):
	if (not hasQuote(item)) and isBookOrMovie(item):
		return False
	if matchKey(item.text, BLACKLIST):
		return False
	if sum(dataCount(item)) < 80: 
		return False
	return True

def isGoodImg(url, check_height = False):
	try:
		image = Image.open(urllib.request.urlopen(url))
		width, height = image.size
		return (not check_height) or height <= 3000
	except:
		return False

@log_on_fail(debug_group)
def postTele(item, sid):
	if not wantSee(item):
		return
	post_link = item.find('span', class_='created_at').find('a')['href']
	quote = item.find('blockquote') or ''
	author = item.find('a', class_='lnk-people').text.strip()
	if quote:
		quote = quote.text.strip() + ' -- ' + author
	if item.find('div', class_='url-block'):
		url = item.find('div', class_='url-block')
		url = url.find('a')['href']
		if len(url) < 80:
			url_text = url
		else:
			url_text = '网页链接'
		try:
			douban_channel.send_message(
				quote + ' [%s](%s)' % (url_text, url), 
				parse_mode='Markdown',
				timeout = 10*60)
		except Exception as e:
			print(e)
			print(quote + ' [%s](%s)' % (url_text, url))
		return
	if item.find('div', class_='pics-wrapper'):
		images = [x['href'].strip() for x in item.find_all('a', class_='view-large') if isGoodImg(x['href'])]
		if len(images) > 0:
			if len(images) > 1 or isGoodImg(images[0], check_height = True):
				group = [InputMediaPhoto(images[0], caption=quote)] + [InputMediaPhoto(url) for url in images[1:]]
				try:
					tele.bot.send_media_group(douban_channel.id, group, timeout = 20*60)
				except Exception as e:
					print(e)
					print(images)

r = None
sids = set()
for page in range(1, page_limit):
	print(page)
	url = 'https://www.douban.com/?p=' + str(page)
	content = getUrl(url)
	b = BeautifulSoup(content, 'html.parser')
	if not r:
		r = BeautifulSoup(content, 'html.parser')
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
		postTele(item, sid) # TODO: dedup
	for x in r.find_all('div', class_='actions'):
		for y in x.find_all('a', class_='btn'):
			y.decompose()
		for y in x.find_all('span', class_='count'):
			y.decompose()
		for y in x.find_all('a'):
			y.string = '----'
	for x in r.find_all('blockquote'):
		x['style'] = "max-height: 400px; display: block;"
	with open('result.html', 'w') as f:
		f.write(str(r))