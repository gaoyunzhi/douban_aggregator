#!/usr/bin/env python3
# -*- coding: utf-8 -*-

BLACKLIST = ['包邮', '闲鱼', '收藏图书到豆列', '关注了成员:', '恶臭扑鼻', 
'过分傻屌', '傻逼无限', '淘宝店', '林爸爸', '求转发', '拙棘', '幸运儿', '转发抽奖']

from bs4 import BeautifulSoup
from telegram_util import matchKey, cutCaption
import sys
import os
import cached_url
from telegram.ext import Updater
from telegram import InputMediaPhoto
import export_to_telegraph
import time
import yaml
import traceback as tb
import pic_cut
import requests

last_request = 0
num_requests = 0

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)
export_to_telegraph.token = credential['telegraph_token']

tele = Updater(credential['bot_token'], use_context=True)
debug_group = tele.bot.get_chat(-1001198682178)
douban_channel = tele.bot.get_chat(-1001206770471)

os.system('touch existing')
with open('existing') as f:
	existing = set(x.strip() for x in f.readlines())

def addToExisting(x):
	x = x.strip()
	if x in existing:
		return False
	existing.add(x)
	with open('existing', 'a') as f:
		f.write('\n' + x)
	return True

def getSoup(url, force_cache=False):
	global num_requests, last_request
	if num_requests < 2:
		num_requests += 1
	else:
		if time.time() - last_request < 5:
			time.sleep(5 + last_request - time.time())
			last_request = time.time()
	return BeautifulSoup(cached_url.get(url, {
		'user-agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
		'cookie': credential['cookie']}, force_cache=force_cache), 'html.parser')

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

def wantSee(item, page):
	if (not hasQuote(item)) and isBookOrMovie(item):
		return False
	if matchKey(item.text, BLACKLIST):
		return False
	if 'people/gyz' in str(item.parent):
		return True
	require = 120 + page
	if 'people/renjiananhuo' in str(item.parent):
		require *= 4 # 这人太火，发什么都有人点赞。。。
	return sum(dataCount(item)) > require

def clearUrl(url):
	if 'weibo' in url:
		index = url.find('?')
		if index > -1:
			url = url[:index]
	if url.endswith('/'):
		url = url[:-1]
	if '_' in url:
		url = '[网页链接](%s)' % url
	url = url.replace('https://', '')
	url = url.replace('http://', '')
	return url

def getQuote(raw_quote):
	if not raw_quote:
		return ''
	quote = raw_quote.text.strip()
	for link in raw_quote.find_all('a', title=True, href=True):
		url = link['title']
		url = clearUrl(export_to_telegraph.export(url) or url)
		quote = quote.replace(link['href'], ' ' + url + ' ')
	return quote

def getReshareInfo(item):
	new_status = item
	while 'new-status' not in new_status.get('class'):
		new_status = new_status.parent
	reshared_by = new_status.find('span', class_='reshared_by')
	if reshared_by:
		return ['reshared_by', reshared_by.find('a')['href']]
	return []

def printDebugInfo(page, post_link, item, quote, suffix):
	print(*([page, post_link] + getReshareInfo(item) + [cutCaption(quote, suffix, 100)]))

def sendMessage(page, quote, suffix, post_link, item):
	printDebugInfo(page, post_link, item, quote, suffix)
	douban_channel.send_message(cutCaption(quote, suffix, 4000), parse_mode='Markdown')
	addToExisting(post_link)

def postTele(page, item):
	post_link = item.find('span', class_='created_at').find('a')['href']
	if post_link.strip() in existing:
		return

	author = item.find('a', class_='lnk-people').text.strip()	
	raw_quote = item.find('blockquote') or ''
	quote = getQuote(raw_quote)

	suffix =  ' [%s](%s)' % (author, post_link)
	if '/status/' in post_link:
		soup = getSoup(post_link, force_cache=True).find('div', class_='status-item')	
		images = [x['src'].strip() for x in soup.find_all('img', class_='upload-pic')]
		images = pic_cut.getCutImages(images)
		if images:
			cap = cutCaption(quote, suffix, 1000)
			group = [InputMediaPhoto(open(images[0], 'rb'), caption=cap, parse_mode='Markdown')] + \
				[InputMediaPhoto(open(x, 'rb')) for x in images[1:]]
			printDebugInfo(page, post_link, item, quote, suffix)
			tele.bot.send_media_group(douban_channel.id, group, timeout = 20*60)
			addToExisting(post_link)
			return

	if '/note/' in post_link:
		url = export_to_telegraph.export(post_link, force=True)
		sendMessage(page, url + ' ' + quote, suffix, post_link, item)
		return

	if quote and raw_quote.find('a', title=True, href=True):
		sendMessage(page, quote, suffix, post_link, item)
		return

	if item.find('div', class_='url-block'):
		url = item.find('div', class_='url-block')
		url = url.find('a')['href']
		url = clearUrl(export_to_telegraph.export(url) or url)
		sendMessage(page, quote, ' ' + url + ' ' + suffix, post_link, item)
		return

def start():
	for page in range(1, 100):
		url = 'https://www.douban.com/?p=' + str(page)
		for item in getSoup(url).find_all('div', class_='status-item'):
			if not wantSee(item, page):
				continue
			postTele(page, item)
		if page % 5 == 0:
			print(page)

if __name__ == '__main__':
	start()