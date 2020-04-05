import os

class DB(object):
	def __init__(self):
		with open('db/config') as f:
			self.config = yaml.load(f, Loader=yaml.FullLoader)
		with open('db/cookie') as f:
			self.cookie = yaml.load(f, Loader=yaml.FullLoader)
		self.existing = {}
		for name in self.getChannels():
			fn = '%s_existing' % name
			os.system('touch %s' % fn)
			with open(fn) as f:
				self.existing[name] = set(x.strip() for x in f.readlines())

	def blacklistAdd(self, channel, word):
		self._initBlacklist(channel)
		self.config[channel]['blacklist'].append(word)
		self._sortBlacklist(channel)
		self._save()

	def blacklistRemove(self, channel, word):
		self._initBlacklist(channel)
		if word in self.config[channel]['blacklist']:
			self.config[channel]['blacklist'].remove(word)
		self._sortBlacklist(channel)
		self._save()

	def getChannels(self):
		return self.cookie.keys()

	def getCookie(self, name):
		return self.cookie.get(name)

	def getBlacklist(self, name):
		self._initBlacklist(name)
		return self.config[name]['blacklist']

	def existing(self, name, x):
		return x.strip() in self.existing[name]

	def addToExisting(self, name, x):
		x = x.strip()
		if x in self.existing[name]:
			return
		self.existing[name].add(x)
		with open('db/%s_existing' % name, 'a') as f:
			f.write('\n' + x)

	def _initBlacklist(self, channel):
		self.config[channel] = self.config.get(channel, {})
		self.config[channel]['blacklist'] = self.config[channel].get('blacklist', [])

	def _sortBlacklist(self, channel):
		self.config[channel]['blacklist'] = 
			sorted(list(set(self.config[channel]['blacklist'])))

	def _save():
		with open('db/config', 'w') as f:
			f.write(yaml.dump(self.config, sort_keys=True, indent=2))
