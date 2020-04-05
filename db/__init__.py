class DB(object):
	def __init__(self):
		with open('db/config') as f:
			self.config = yaml.load(f, Loader=yaml.FullLoader)

	def blacklistAdd(self, channel, word):
		self._initBlacklist(channel)
		self.config[channel]['backlist'].append(word)
		self._sortBlacklist(channel)
		self._save()

	def blacklistRemove(self, channel, word):
		self._initBlacklist(channel)
		if word in self.config[channel]['backlist']:
			self.config[channel]['backlist'].remove(word)
		self._sortBlacklist(channel)
		self._save()

	def _initBlacklist(self, channel):
		self.config[channel] = self.config.get(channel, {})
		self.config[channel]['backlist'] = self.config[channel].get('backlist', [])

	def _sortBlacklist(self, channel):
		self.config[channel]['backlist'] = sorted(list(set(self.config[channel]['backlist'])))

	def _save():
		with open('db/config', 'w') as f:
			f.write(yaml.dump(self.config, sort_keys=True, indent=2))
