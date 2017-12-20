# encoding: UTF-8

from Api import *

########################################################################
class Okex(Api):
	def __init__(self, spi):
		Api.__init__(self, spi)
		self.name = 'okex'

	def evt2str(self, evt):
		try:
			# 创建解压器
			decompress = zlib.decompressobj(-zlib.MAX_WBITS)
			# 将原始数据解压成字符串
			inflated = decompress.decompress(evt) + decompress.flush()
			# 通过json解析字符串
			data = json.loads(inflated)
			return data

		except zlib.error as err:
			# print err
			# # 创建解压器
			# decompress = zlib.decompressobj(16+zlib.MAX_WBITS)
			# # 将原始数据解压成字符串
			# inflated = decompress.decompress(evt) + decompress.flush()
			# 通过json解析字符串
			data = json.loads(evt)
			return data


	# ----------------------------------------------------------------------
	def generateSign(self, params):
		"""生成签名"""
		l = []
		for key in sorted(params.keys()):
			l.append('%s=%s' % (key, params[key]))
		l.append('secret_key=%s' % self.secretKey)
		sign = '&'.join(l)
		return hashlib.md5(sign.encode('utf-8')).hexdigest().upper()

	# ----------------------------------------------------------------------
	def sendMarketDataRequest(self, channel):
		"""发送行情请求"""
		# 生成请求
		d = {}
		d['event'] = 'addChannel'
		d['binary'] = True
		d['channel'] = channel

		# 使用json打包并发送
		j = json.dumps(d)

		# 若触发异常则重连
		try:
			self.ws.send(j)
		except websocket.WebSocketConnectionClosedException:
			pass

	# ----------------------------------------------------------------------
	def sendTradingRequest(self, channel, params):
		"""发送交易请求"""
		# 在参数字典中加上api_key和签名字段
		params['api_key'] = self.apiKey
		params['sign'] = self.generateSign(params)

		# 生成请求
		d = {}
		d['event'] = 'addChannel'
		d['binary'] = True
		d['channel'] = channel
		d['parameters'] = params

		# 使用json打包并发送
		j = json.dumps(d)

		# 若触发异常则重连
		try:
			self.ws.send(j)
		except websocket.WebSocketConnectionClosedException:
			pass


	## 现货相关
	#######################

	# ----------------------------------------------------------------------
	def subscribeSpotTicker(self, symbol):
		"""订阅现货普通报价"""
		self.sendMarketDataRequest('ok_sub_spot%s_%s_ticker' % (self.currency, symbol))

	# ----------------------------------------------------------------------
	def subscribeSpotDepth(self, symbol, depth):
		"""订阅现货深度报价"""
		self.sendMarketDataRequest('ok_sub_spot%s_%s_depth_%s' % (self.currency, symbol, depth))

	def subscribeSpotTradeData(self, symbol):
		"""订阅现货成交记录"""
		self.sendMarketDataRequest('ok_sub_spot%s_%s_trades' % (self.currency, symbol))

	# ----------------------------------------------------------------------
	def subscribeSpotKline(self, symbol, interval):
		"""订阅现货K线"""
		self.sendMarketDataRequest('ok_sub_spot%s_%s_kline_%s' % (self.currency, symbol, interval))

	# ----------------------------------------------------------------------
	def spotTrade(self, symbol, type_, price, amount):
		"""现货委托"""
		params = {}
		params['symbol'] = str(symbol + self.currency)
		params['type'] = str(type_)
		params['price'] = str(price)
		params['amount'] = str(amount)
		# print params
		channel = 'ok_spot%s_trade' % (self.currency)

		self.sendTradingRequest(channel, params)

	# ----------------------------------------------------------------------
	def spotCancelOrder(self, symbol, orderid):
		"""现货撤单"""
		params = {}
		params['symbol'] = str(symbol + self.currency)
		params['order_id'] = str(orderid)

		channel = 'ok_spot%s_cancel_order' % (self.currency)

		self.sendTradingRequest(channel, params)

	# ----------------------------------------------------------------------
	def spotUserInfo(self):
		"""查询现货账户"""
		channel = 'ok_spot%s_userinfo' % (self.currency)

		self.sendTradingRequest(channel, {})

	# ----------------------------------------------------------------------
	def spotOrderInfo(self, symbol, orderid):
		"""查询现货委托信息"""
		params = {}
		params['symbol'] = str(symbol + self.currency)
		params['order_id'] = str(orderid)

		channel = 'ok_spot%s_orderinfo' % (self.currency)

		self.sendTradingRequest(channel, params)

	# ----------------------------------------------------------------------
	def subscribeSpotTrades(self):
		"""订阅现货成交信息"""
		channel = 'ok_sub_spot%s_trades' % (self.currency)

		self.sendTradingRequest(channel, {})


if __name__ == '__main__':
	spi = Spi()
	api = Okex(spi)
	api.connect()
	sleep(100)
	# while 1:
	# 	input = raw_input('0.连接 1:订阅tick 2.订阅depth 3.订阅成交记录 4.订阅K线 5.下单 6.撤单 7.查账户 8.查订单 9.订阅交易数据 10.订阅账户 20.断开连接\n')
	# 	if input == '0':
	# 		api.connect(host, apiKey, secretKey, trace=False)
	# 		sleep(2)
	# 	elif input == '1':
	# 		api.subscribeSpotTicker('btc')
	# 	elif input == '2':
	# 		api.subscribeSpotDepth('btc', 20)
	# 	elif input == '3':
	# 		api.subscribeSpotTrades()
	# 	elif input == '4':
	# 		api.subscribeSpotKline('btc', INTERVAL_1M)
	# 	elif input == '5':
	# 		# api.spotTrade('btc_', 'buy', str(17000), str(0.01))
	# 		# api.spotTrade('btc_', 'buy', str(16000), str(0.01))
	# 		pass
	# 	elif input == '6':
	# 		pass
	# 	elif input == '7':
	# 		api.spotUserInfo()
	# 	elif input == '8':
	# 		api.spotOrderInfo('btc', '-1')
	# 	elif input == '9':
	# 		api.subscribeSpotTrades()
	# 	elif input == '10':
	# 		api.subscribeSpotUserInfo()
	# 	elif input == '20':
	# 		api.close()
	# 	else:
	# 		break
