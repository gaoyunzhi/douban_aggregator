#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from readability import Document
from .title import _findTitle
from .author import _findAuthor
from .content import _findMain
import hashlib
import sys

def _getUrlContent(url):
	headers = {
		'method': 'GET',
		'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
		'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
	}
	return requests.get(url, headers=headers).text