# encoding: UTF-8

import hashlib
import zlib
import json
from time import sleep
from threading import Thread
import websocket
from abc import ABCMeta, abstractmethod
import sys
sys.path.append('.')
sys.path.append('..')
from prj.common.function import *

class Spi(object):
	# __metaclass__ = ABCMeta 

	def __init__(self):
		self.api = None

	# @abstractmethod
	def onMessage(self, ws, evt):
		print 'onMessage'
		data = self.api.evt2str(evt)
		# print data[0]['channel'], data

	# @abstractmethod
	def onError(self, ws, evt):
		"""错误推送"""
		print 'onError'
		print evt

	# @abstractmethod
	def onClose(self, ws):
		"""接口断开"""
		print 'onClose'

	# @abstractmethod
	def onOpen(self, ws):
		"""接口打开"""
		print 'onOpen'


class Api(object):
	__metaclass__ = ABCMeta 

	def __init__(self, spi):
		self.name = '' # 交易所的名字
		self.rest_url = ''  
		self.websocket_future_url = ''  
		self.websocket_url = ''  
		self.api_key = ''  
		self.secret_key = ''  
		self.url = '' # 从上面3个url取其一，优先websocket，其次rest，目前不做期货
		self.ws = None  # websocket应用对象
		self.thread = None  # 工作线程
		self.spi = spi
		self.spi.api = self

	def connect(self):
		# 读配置
		p = getRootPath()+'/cfg/accounts.json'
		f = open(p)
		j = json.load(f)
		s = j[self.name]
		self.rest_url = s['rest_url']
		self.websocket_future_url = s['websocket_future_url']
		self.websocket_url = s['websocket_url']
		self.api_key = s['api_key']
		self.secret_key = s['secret_key']

		websocket.enableTrace(False)
		self.url = self.websocket_url
		if not self.url:
			self.url = self.rest_url
		self.ws = websocket.WebSocketApp(self.url,
										on_message=self.spi.onMessage,
										on_error=self.spi.onError,
										on_close=self.spi.onClose,
										on_open=self.spi.onOpen)

		self.thread = Thread(target=self.ws.run_forever)
		self.thread.start()


	def close(self):
		if self.thread and self.thread.isAlive():
			self.ws.close()
			self.thread.join()


	def reconnect(self):
		self.close()

		self.ws = websocket.WebSocketApp(self.url,
										on_message=self.spi.onMessage,
										on_error=self.spi.onError,
										on_close=self.spi.onClose,
										on_open=self.spi.onOpen)

		self.thread = Thread(target=self.ws.run_forever)
		self.thread.start()

	def evt2str(self, evt):
		pass

	def send_request(self, request):
		try:
			self.ws.send(request)
		except websocket.WebSocketConnectionClosedException:
			# 若触发异常则重连
			self.reconnect(self)