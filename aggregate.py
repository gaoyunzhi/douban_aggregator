#!/usr/bin/env python3
# -*- coding: utf-8 -*-

BLACKLIST = ['包邮', '闲鱼', '收藏图书到豆列', '关注了成员:', '恶臭扑鼻', 
'过分傻屌', '傻逼无限', '淘宝店', '林爸爸', '求转发', '拙棘', '幸运儿']

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
	return sum(dataCount(item)) > 120 + page * 5

def getQuote(raw_quote):
	if not raw_quote:
		return ''
	quote = raw_quote.text.strip()
	for link in raw_quote.find_all('a', title=True, href=True):
		url = link['title']
		url = export_to_telegraph.export(url) or url
		if 'weibo' in url:
			index = url.find('?')
			if index > -1:
				url = url[:index]
		if '_' in url:
			url = '[网页链接](%s)' % url
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

def sendMessage(page, quote, suffix, post_link):
	print(page, cut(quote, suffix, 4000))
	douban_channel.send_message(cut(quote, suffix, 4000), parse_mode='Markdown')
	addToExisting(post_link)

def canSend(image):
	try:
		r = debug_group.send_photo(image)
		r.delete()
		return True
	except:
		return False

# @log_on_fail(debug_group)
def postTele(page, item):
	post_link = item.find('span', class_='created_at').find('a')['href']
	if post_link.strip() in existing:
		return

	author = item.find('a', class_='lnk-people').text.strip()	
	raw_quote = item.find('blockquote') or ''
	quote = getQuote(raw_quote)

	new_status = item
	while 'new-status' not in new_status.get('class'):
		new_status = new_status.parent
	reshared_by = new_status.find('span', class_='reshared_by')
	if reshared_by:
		print('reshared_by', reshared_by.find('a')['href'])
		pass

	suffix =  ' [%s](%s)' % (author, post_link)
	if '/status/' in post_link:
		soup = getSoup(post_link).find('div', class_='status-item')	
		images = [x['href'].strip() for x in soup.find_all('a', class_='view-large')]
		images = [x for x in images if canSend(x)]
		images = images[:9]
		raw_images = images[:]
		if images:
			cap = cut(quote, suffix, 1000)
			group = [InputMediaPhoto(images[0], caption=cap, parse_mode='Markdown')] + \
				[InputMediaPhoto(url) for url in images[1:]]
			print(raw_images)
			print(page, post_link, cap)
			tele.bot.send_media_group(douban_channel.id, group, timeout = 20*60)
			addToExisting(post_link)
			return

	if '/note/' in post_link:
		url = export_to_telegraph.export(post_link, force=True)
		sendMessage(page, url + ' ' + quote, suffix, post_link)
		return

	if quote and raw_quote.find('a', title=True, href=True):
		sendMessage(page, quote, suffix, post_link)
		return

	if item.find('div', class_='url-block'):
		print('MORE', page, post_link)
		# print('here')
		# url = item.find('div', class_='url-block')
		# url = url.find('a')['href']
		# url = export_to_telegraph.export(url) or url
		# if len(url) < 80:
		# 	url_text = url
		# else:
		# 	url_text = '网页链接'
		# return douban_channel.send_message(
		# 	quote + ' [%s](%s) [%s](%s)' % (url_text, url, author, post_link), 
		# 	parse_mode='Markdown',
		# 	timeout = 10*60)

def start():
	for page in range(1, 50):
		url = 'https://www.douban.com/?p=' + str(page)
		for item in getSoup(url).find_all('div', class_='status-item'):
			if not wantSee(item, page):
				continue
			postTele(page, item)
		if page % 5 == 0:
			print(page)
			time.sleep(page % 31)

if __name__ == '__main__':
	start()