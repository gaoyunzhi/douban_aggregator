#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from telegram_util import matchKey, cutCaption, clearUrl
import sys
import os
import cached_url
from telegram.ext import Updater
import export_to_telegraph
import time
import yaml
import web_2_album
import random
import album_sender

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
	existing.add(x)
	with open('existing', 'a') as f:
		f.write('\n' + x)

def getSoup(url, force_cache=False):
	global num_requests, last_request
	num_requests += 1
	wait = min(random.random() * 10, num_requests / 5 * random.random())
	if time.time() - last_request < wait:
		time.sleep(wait + last_request - time.time())
	last_request = time.time()
	return BeautifulSoup(cached_url.get(url, {
		'cookie': credential['cookie']}, force_cache=force_cache), 'html.parser')

def dataCount(item):
	for x in item.find_all('span', class_='count'):
		r = int(x.get('data-count'))
		if r:
			yield r

def wantSee(item, page):
	if 'people/gyz' in str(item.parent):
		return True
	if matchKey(str(item), BLACKLIST):
		return False
	require = 120 + page
	if 'people/renjiananhuo' in str(item.parent):
		require *= 4 # 这人太火，发什么都有人点赞。。。
	return sum(dataCount(item)) > require

def getSource(item):
	new_status = item
	while 'new-status' not in new_status.get('class'):
		new_status = new_status.parent
	for d in new_status.find_all('div'):
		if d.attrs:
			url = d.get('data-status-url', '').strip()
			if url:
				return url

def getCap(quote, url):
	if '_' in url:
		url = '[%s](%s)' % (url, url)
	return cutCaption(quote, url, 4000)

def getResult(post_link, item):
	raw_quote = item.find('blockquote') or ''
	quote = export_to_telegraph.exportAllInText(raw_quote)

	r = web_2_album.Result()

	if '/status/' in post_link:
		r = web_2_album.get(post_link, force_cache=True)
		r.cap = quote
		if r.imgs:
			print(post_link, r.imgs, r.cap)
			return r

	note = item.find('div', class_='note-block')
	if note:
		note = note['data-url']
		url = export_to_telegraph.export(note, force=True)
		r.cap = getCap(quote, url)
		return r

	if quote and raw_quote.find('a', title=True, href=True):
		r.cap = quote
		return r

	if item.find('div', class_='url-block'):
		url = item.find('div', class_='url-block')
		url = url.find('a')['href']
		url = clearUrl(export_to_telegraph.export(url) or url)
		r.cap = getCap(quote, url)
		return r

def postTele(page, item):
	post_link = item.find('span', class_='created_at').find('a')['href']
	source = getSource(item) or post_link

	if source.strip() in existing:
		return 'existing'
	if post_link.strip() in existing:
		return 'repeated_share'

	result = getResult(post_link, item)
	if result:
		album_sender.send(douban_channel, source, result)
		addToExisting(post_link)
		addToExisting(source)
		return 'sent'

def removeOldFiles(d):
	for x in os.listdir(d):
		if os.path.getmtime(d + '/' + x) < time.time() - 60 * 60 * 72:
			os.system('rm ' + d + '/' + x)

def loopImp():
	removeOldFiles('tmp')
	removeOldFiles('tmp_image')
	existing = 0
	try:
		start = int(sys.argv[1])
	except:
		start = 1
	for page in range(start, 100):
		url = 'https://www.douban.com/?p=' + str(page)
		items = list(getSoup(url).find_all('div', class_='status-item'))
		if not items:
			break
		for item in items:
			if not wantSee(item, page):
				continue
			r = postTele(page, item)
			if r == 'existing':
				existing += 1
			elif r == 'sent':
				existing = 0
			if existing > 20 or page * existing > 500:
				return # heuristic
		if page % 5 == 0:
			print(page)

def loop():
	loopImp()
	threading.Timer(60 * 60 * 2, loop).start() 

threading.Timer(1, loop).start()

@log_on_fail(debug_group)
def private(update, context):
	update.message.reply_text('Add me to public channel, then use /d_sc to set your douban cookie')

tele.dispatcher.add_handler(MessageHandler(Filters.text & Filters.private, private))

tele.start_polling()
tele.idle()