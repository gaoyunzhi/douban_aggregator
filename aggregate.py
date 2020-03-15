#!/usr/bin/env python3
# -*- coding: utf-8 -*-

BLACKLIST = ['包邮', '闲鱼', '收藏图书到豆列', '关注了成员:', '恶臭扑鼻', 
'过分傻屌', '傻逼无限', '淘宝店', '林爸爸', '求转发', '拙棘', '幸运儿', '转发抽奖']

from bs4 import BeautifulSoup
from telegram_util import matchKey
import sys
import os
import cached_url
from telegram.ext import Updater
from telegram import InputMediaPhoto
from telegram_util import log_on_fail
import export_to_telegraph
import time
import yaml
import traceback as tb
import pic_cut

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

def getSoup(url):
	time.sleep(5)
	return BeautifulSoup(cached_url.get(url, {
		'user-agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
		'cookie': credential['cookie']}), 'html.parser')

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
	return sum(dataCount(item)) > 120 + page

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

def cut(quote, suffix, limit):
	if len(quote) + len(suffix) > limit:
		result = quote[:limit - len(suffix)] + '...' + suffix
	else:
		result = quote + suffix
	result = result.replace('https://', '')
	result = result.replace('http://', '')
	return result

def getReshareInfo(item):
	new_status = item
	while 'new-status' not in new_status.get('class'):
		new_status = new_status.parent
	reshared_by = new_status.find('span', class_='reshared_by')
	if reshared_by:
		return ['reshared_by', reshared_by.find('a')['href']]
	return []

def printDebugInfo(page, post_link, item, quote, suffix):
	print(*([page, post_link] + getReshareInfo(item) + [cut(quote, suffix, 100)]))

def sendMessage(page, quote, suffix, post_link, item):
	printDebugInfo(page, post_link, item, quote, suffix)
	douban_channel.send_message(cut(quote, suffix, 4000), parse_mode='Markdown')
	addToExisting(post_link)

def getSend(image):
	os.system('mkdir tmp_image > /dev/null 2>&1')
	time.sleep(1)
	try:
		with open('tmp_image/1', 'wb') as f:
			f.write(requests.get(image, stream=True))
		cuts = [open(x, 'rb') for x in pic_cut.cut('1')]
		if not cuts:
			cuts = [image]
		for cut in cuts:
			try:
				r = debug_group.send_photo(cut, timeout = 2*60)
				yield cut
				r.delete()
			except Exception as e:
				print(image, str(e))
			try:
				r.delete()
			except Exception as e:
				pass
	except Exception as e:
		print(image, str(e))
		pass

	os.system('rm -r tmp_image > /dev/null 2>&1')
	return result


# @log_on_fail(debug_group)
def postTele(page, item):
	post_link = item.find('span', class_='created_at').find('a')['href']
	if post_link.strip() in existing:
		return

	author = item.find('a', class_='lnk-people').text.strip()	
	raw_quote = item.find('blockquote') or ''
	quote = getQuote(raw_quote)

	suffix =  ' [%s](%s)' % (author, post_link)
	if '/status/' in post_link:
		soup = getSoup(post_link).find('div', class_='status-item')	
		images = [x['href'].strip() for x in soup.find_all('a', class_='view-large')]
		images = [y for y in getSend(x) for x in images]
		images = images[:9]
		raw_images = images[:]
		if images:
			cap = cut(quote, suffix, 1000)
			group = [InputMediaPhoto(images[0], caption=cap, parse_mode='Markdown')] + \
				[InputMediaPhoto(url) for url in images[1:]]
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
	for page in range(1, 50):
		url = 'https://www.douban.com/?p=' + str(page)
		for item in getSoup(url).find_all('div', class_='status-item'):
			if not wantSee(item, page):
				continue
			postTele(page, item)
		if page % 5 == 0:
			print(page)

if __name__ == '__main__':
	start()