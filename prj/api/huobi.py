# encoding: UTF-8

import urllib
import hashlib
import hmac
import base64
import json
import requests
from time import time, sleep
from Queue import Queue, Empty
from threading import Thread
import io
import gzip
import websocket
import datetime

from Api import *


# 火币
class Huobi(Api):

    def __init__(self, spi):
		Api.__init__(self, spi)
		self.name = 'huobi'

    def evt2str(self, evt):
        g = gzip.GzipFile(fileobj=io.BytesIO(evt))
        data = g.read().decode('utf-8')
        return data

    
    def generateSign(self, params):
        """生成签名"""
        params = sorted(params.iteritems(), key=lambda d: d[0], reverse=False)
        message = urllib.urlencode(params)

        m = hashlib.md5()
        m.update(message)
        m.digest()

        sig = m.hexdigest()
        return sig

    # 实时行情websocket接口
    def SubMarketKline(self, symbol, period):
        """订阅k线"""
        d = {}
        d['sub'] = 'market.%s.kline.%s' % (symbol, period)
        d['id'] = 'sub_kline_%s_%s' % (symbol, period)
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

    def ReqMarketKline(self, symbol, period, start_date=None, end_date=None):
        """请求k线"""
        d = {}
        d['req'] = 'market.%s.kline.%s' % (symbol, period)
        d['id'] = 'req_kline_%s_%s' % (symbol, period)
        if start_date is not None:
            d['from'] = start_date
        if end_date is not None:
            d['to'] = end_date
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

    def SubMarketDepth(self, symbol, tp='step0'):
        """"订阅深度"""
        d = {}
        d['sub'] = 'market.%s.depth.%s' % (symbol, tp)
        d['id'] = 'sub_depth_%s_%s' % (symbol, tp)
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

    def ReqMarketDepth(self, symbol, tp='step0'):
        """请求深度"""
        d = {}
        d['req'] = 'market.%s.depth.%s' % (symbol, tp)
        d['id'] = 'req_depth_%s_%s' % (symbol, tp)
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

    def SubTradeDetail(self, symbol):
        """请求深度"""
        d = {}
        d['sub'] = 'market.%s.trade.detail' % symbol
        d['id'] = 'sub_trade_detail_%s' % symbol
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)

    def ReqTradeDetail(self, symbol):
        """请求深度"""
        d = {}
        d['req'] = 'market.%s.trade.detail' % symbol
        d['id'] = 'req_trade_detail_%s' % symbol
        j = json.dumps(d)
        try:
            self.ws.send(j)
        except websocket.WebSocketConnectionClosedException:
            self.reconnect()
            self.ws.send(j)
        url = '%s/common/symbols' % HUOBI_RESTT

if __name__ == '__main__':
    apiKey = "f0de6392-af55feb2-e7e5bda9-31b50"
    secretKey = "cfe1646d-ff5a4f48-80c8b8a0-a2a18"

    # api = DataAPI()
    # host = HUOBI_WS

    # api.connect(host, apiKey, secretKey, trace=False)
    # sleep(2)
    
    # api.SubMarketKline('ethusdt','1min')
    # api.SubMarketDepth('ethusdt','step0')
    # api.SubTradeDetail('ethusdt')
    # api.ReqMarketKline('ethusdt','1min')
