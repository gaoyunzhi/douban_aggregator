from bs4 import BeautifulSoup
import cached_url
import time
import random

class SoupGet(object):
	def __init__(self):
		self.reset()

	def reset(self):
		self.num_requests = 0
		self.last_request = 0

	def getSoup(url, force_cache=False):
		self.num_requests += 1
		wait = min(random.random() * 10, self.num_requests / 5 * random.random())
		if time.time() - self.last_request < wait:
			time.sleep(wait + self.last_request - time.time())
		self.last_request = time.time()
		return BeautifulSoup(cached_url.get(url, {
			'cookie': credential['cookie']}, force_cache=force_cache), 'html.parser')