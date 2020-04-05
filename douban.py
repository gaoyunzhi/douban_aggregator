#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import matchKey, cutCaption, clearUrl, splitCommand, autoDestroy, log_on_fail
import sys
import os
from telegram.ext import Updater, MessageHandler, Filters
import export_to_telegraph
import time
import yaml
import web_2_album
import album_sender
from soup_get import SoupGet
from db import DB
import threading

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)
export_to_telegraph.token = credential['telegraph_token']

tele = Updater(credential['bot_token'], use_context=True)
debug_group = tele.bot.get_chat(-1001198682178)

sg = SoupGet()
db = DB()

def dataCount(item):
	for x in item.find_all('span', class_='count'):
		r = int(x.get('data-count'))
		if r:
			yield r

def wantSee(item, page, channel_name):
	if 'people/gyz' in str(item.parent):
		return True
	if matchKey(str(item), db.getBlacklist(channel_name)):
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

def postTele(douban_channel, item):
	post_link = item.find('span', class_='created_at').find('a')['href']
	source = getSource(item) or post_link

	if db.exist(douban_channel.username, source.strip()):
		return 'repeated_share'
	if db.exist(douban_channel.username, post_link.strip()):
		return 'existing'

	result = getResult(post_link, item)
	if result:
		album_sender.send(douban_channel, source, result)
		db.addToExisting(douban_channel.username, post_link)
		db.addToExisting(douban_channel.username, source)
		return 'sent'

@log_on_fail(debug_group)
def processChannel(name):
	# TODO: revisit fetch wrong status issue
	existing = 0
	try:
		start = int(sys.argv[1])
	except:
		start = 1
	print('start processing %s' % name)

	douban_channel = tele.bot.get_chat('@' + name)
	for page in range(start, 100):
		url = 'https://www.douban.com/?p=' + str(page)
		items = list(sg.getSoup(url, db.getCookie(name))
			.find_all('div', class_='status-item'))
		if not items:
			debug_group.send_message('Cookie expired for channel: %s' % name)
			return
		for item in items:
			if not wantSee(item, page, name):
				continue
			r = postTele(douban_channel, item)
			if r == 'sent' and 'skip' in sys.argv:
				return # testing mode, only send one message
			if r == 'existing':
				existing += 1
			elif r == 'sent':
				existing = 0
		if existing > 10 or page * existing > 200:
			break
	print('channel %s finished by %d page' % (name, page))

def removeOldFiles(d):
	for x in os.listdir(d):
		if os.path.getmtime(d + '/' + x) < time.time() - 60 * 60 * 72:
			os.system('rm ' + d + '/' + x)

def loopImp():
	removeOldFiles('tmp')
	removeOldFiles('tmp_image')
	sg.reset()
	for name in db.getChannels():
		processChannel(name)

def loop():
	loopImp()
	threading.Timer(60 * 60 * 2, loop).start() 

threading.Timer(1, loop).start()

@log_on_fail(debug_group)
def private(update, context):
	update.message.reply_text('Add me to public channel, then use /d_sc to set your douban cookie')

def commandInternal(msg):
	command, text = splitCommand(msg.text)
	if matchKey(command, ['/d_sc', 'set_cookie']):
		return db.setCookie(msg.chat.username, text)
	if matchKey(command, ['/d_ba', 'blacklist_ba']):
		return db.blacklistAdd(msg.chat.username, text)
	if matchKey(command, ['/d_br', 'blacklist_br']):
		return db.blacklistRemove(msg.chat.username, text)
	if matchKey(command, ['/d_bl', 'blacklist_list']):
		return 'blacklist:\n' + '\n'.join(db.getBlacklist(msg.chat.username))

@log_on_fail(debug_group)
def command(update, context):
	msg= update.channel_post
	if not msg.text.startswith('/d'):
		return
	r = commandInternal(msg)
	if not r:
		return
	autoDestroy(msg.reply_text(r), 0.1)
	msg.delete()

tele.dispatcher.add_handler(MessageHandler(
	Filters.text & Filters.private, private))
tele.dispatcher.add_handler(MessageHandler(
	Filters.update.channel_post & Filters.command, command))

tele.start_polling()
tele.idle()