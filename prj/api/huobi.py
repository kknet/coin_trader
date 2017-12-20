# encoding: UTF-8

import hashlib
import zlib
import json
from time import sleep
from threading import Thread

import websocket

# HUOBI API 地址
HUOBI_WS = 'wss://api.huobi.pro/ws'    # 国内服务器
HUOBI_RESTM = 'https;//api.huobi.pro/market'  # rest行情
HUOBI_RESTT = 'https://api.huobi.pro/v1'     # rest交易

#%%
########################################################################
class HuobiApi(object):
	"""基于Websocket的API对象"""

	# ----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		self.apiKey = ''  # 用户名
		self.secretKey = ''  # 密码
		self.host = ''  # 服务器地址

		self.currency = ''  # 货币类型（usd或者cny）

		self.ws = None  # websocket应用对象
		self.thread = None  # 工作线程

	#######################
	## 通用函数
	#######################

	# ----------------------------------------------------------------------
	def readData(self, evt):
		"""解压缩推送收到的数据"""
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
	def onMessage(self, ws, evt):
		"""信息推送"""
		print('onMessage')
		data = self.readData(evt)
		print(data[0]['channel'], data)

	# ----------------------------------------------------------------------
	def onError(self, ws, evt):
		"""错误推送"""
		print('onError')
		print(evt)

	# ----------------------------------------------------------------------
	def onClose(self, ws):
		"""接口断开"""
		print('onClose')

	# ----------------------------------------------------------------------
	def onOpen(self, ws):
		"""接口打开"""
		print('onOpen')

	# ----------------------------------------------------------------------
	def connect(self, host, apiKey, secretKey, trace=False):
		"""连接服务器"""
		self.host = host
		self.apiKey = apiKey
		self.secretKey = secretKey

#		if self.host == OKCOIN_CNY:
#			self.currency = CURRENCY_CNY
#		else:
#			self.currency = CURRENCY_USD

		websocket.enableTrace(trace)

		self.ws = websocket.WebSocketApp(host,
										 on_message=self.onMessage,
										 on_error=self.onError,
										 on_close=self.onClose,
										 on_open=self.onOpen)

		self.thread = Thread(target=self.ws.run_forever)
		self.thread.start()

	# ----------------------------------------------------------------------
	def reconnect(self):
		"""重新连接"""
		# 首先关闭之前的连接
		self.close()

		# 再执行重连任务
		self.ws = websocket.WebSocketApp(self.host,
										 on_message=self.onMessage,
										 on_error=self.onError,
										 on_close=self.onClose,
										 on_open=self.onOpen)

		self.thread = Thread(target=self.ws.run_forever)
		self.thread.start()

	# ----------------------------------------------------------------------
	def close(self):
		"""关闭接口"""
		if self.thread and self.thread.isAlive():
			self.ws.close()
			self.thread.join()

	# ----------------------------------------------------------------------
	def sendMarketDataRequest(self, symbol, period):
		"""发送行情请求"""
		# 生成请求
		d = {}
		d['sub'] = 'market.%s.kline.%s' % (symbol, period)
		d['id'] = 'aflajdadf'

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

			#######################

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

		# ----------------------------------------------------------------------

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

	# ----------------------------------------------------------------------
	def subscribeSpotUserInfo(self):
		"""订阅现货账户信息"""
		channel = 'ok_sub_spot%s_userinfo' % (self.currency)

		self.sendTradingRequest(channel, {})

	#######################
	## 期货相关
	#######################

	# ----------------------------------------------------------------------
	def subscribeFutureTicker(self, symbol, expiry):
		"""订阅期货普通报价"""
		self.sendMarketDataRequest('ok_sub_future%s_%s_ticker_%s' % (self.currency, symbol, expiry))

	# ----------------------------------------------------------------------
	def subscribeFutureDepth(self, symbol, expiry, depth):
		"""订阅期货深度报价"""
		self.sendMarketDataRequest('ok_sub_future%s_%s_depth_%s_%s' % (self.currency, symbol,
																	   expiry, depth))

		# ----------------------------------------------------------------------

	def subscribeFutureTradeData(self, symbol, expiry):
		"""订阅期货成交记录"""
		self.sendMarketDataRequest('ok_sub_future%s_%s_trade_%s' % (self.currency, symbol, expiry))

	# ----------------------------------------------------------------------
	def subscribeFutureKline(self, symbol, expiry, interval):
		"""订阅期货K线"""
		self.sendMarketDataRequest('ok_sub_future%s_%s_kline_%s_%s' % (self.currency, symbol,
																	   expiry, interval))

	# ----------------------------------------------------------------------
	def subscribeFutureIndex(self, symbol):
		"""订阅期货指数"""
		self.sendMarketDataRequest('ok_sub_future%s_%s_index' % (self.currency, symbol))

	# ----------------------------------------------------------------------
	def futureTrade(self, symbol, expiry, type_, price, amount, order, leverage):
		"""期货委托"""
		params = {}
		params['symbol'] = str(symbol + self.currency)
		params['type'] = str(type_)
		params['price'] = str(price)
		params['amount'] = str(amount)
		params['contract_type'] = str(expiry)
		params['match_price'] = str(order)
		params['lever_rate'] = str(leverage)

		channel = 'ok_future%s_trade' % (self.currency)

		self.sendTradingRequest(channel, params)

	# ----------------------------------------------------------------------
	def futureCancelOrder(self, symbol, expiry, orderid):
		"""期货撤单"""
		params = {}
		params['symbol'] = str(symbol + self.currency)
		params['order_id'] = str(orderid)
		params['contract_type'] = str(expiry)

		channel = 'ok_future%s_cancel_order' % (self.currency)

		self.sendTradingRequest(channel, params)

	# ----------------------------------------------------------------------
	def futureUserInfo(self):
		"""查询期货账户"""
		channel = 'ok_future%s_userinfo' % (self.currency)

		self.sendTradingRequest(channel, {})

	# ----------------------------------------------------------------------
	def futureOrderInfo(self, symbol, expiry, orderid, status, page, length):
		"""查询期货委托信息"""
		params = {}
		params['symbol'] = str(symbol + self.currency)
		params['order_id'] = str(orderid)
		params['contract_type'] = expiry
		params['status'] = status
		params['current_page'] = page
		params['page_length'] = length

		channel = 'ok_future%s_orderinfo' % (self.currency)

		self.sendTradingRequest(channel, params)

	# ----------------------------------------------------------------------
	def subscribeFutureTrades(self):
		"""订阅期货成交信息"""
		channel = 'ok_sub_future%s_trades' % (self.currency)

		self.sendTradingRequest(channel, {})

	# ----------------------------------------------------------------------
	def subscribeFutureUserInfo(self):
		"""订阅期货账户信息"""
		channel = 'ok_sub_future%s_userinfo' % (self.currency)

		self.sendTradingRequest(channel, {})

	# ----------------------------------------------------------------------
	def subscribeFuturePositions(self):
		"""订阅期货持仓信息"""
		channel = 'ok_sub_future%s_positions' % (self.currency)

		self.sendTradingRequest(channel, {})

#%%
if __name__ == '__main__':
    #%%
    api = HuobiApi()
    host = HUOBI_WS
    apiKey = "e0287d38-1622d91a-f7c26e77-f7104"
    secretKey = "dba39d1c-33913d36-f248733f-d5846"


    api.connect(host, apiKey, secretKey, trace=False)
    sleep(2)
    
    api.sendMarketDataRequest('btcusdt', '1min')
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