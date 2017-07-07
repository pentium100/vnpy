# encoding: UTF-8

"""
差价交易计算二个合约当前可成交价格的最新差价。
 做多价差策略
"""

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import *
import datetime
from vnpy.trader.app.ctaStrategy.ctaBase import *
from vnpy.trader.vtEvent import *
from vnpy.trader.app.ctaStrategy.ctaTemplate import CtaTemplate
from vnpy.event.eventEngine import Event
from vnpy.trader.app.ctaStrategy.SmsEventData import SmsEventData
from vnpy.trader.app.ctaStrategy.ctaSms import EVENT_CTA_SMS


########################################################################
class SpreadHCRBStrategy(CtaTemplate):
    """二腿合约价差计算"""
    className = 'SpreadHCRBStrategy'
    author = u'clw@itg'


    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'vtSymbol',
                 'volumes',
                 'maxGroupPerTrade',
                 'notifyTo',
                 'openPrice',
                 'closePrice',
                 'slippages',
                 'priceGaps',
                 'maxOpenVolume',
                 'maxCloseVolume',
                 "marginRates",
                 "qtyPerHands",
                 "reverseDeposit"
                 ]

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'openSpread',
               'closeSpread',
               'openVolume',
               'closeVolume',
               'available'
               ]


    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(SpreadHCRBStrategy, self).__init__(ctaEngine, setting)
        self.vtSymbols = setting['vtSymbol'].split(u',')

        # 策略参数

        self.direction1 = CTAORDER_BUY  # 合约1方向
        self.direction2 = CTAORDER_SHORT  # 合约2方向

        # 策略变量
        self.openSpread = EMPTY_FLOAT  # 最新可成交差价
        self.closeSpread = EMPTY_FLOAT  # 最新可成交差价
        self.openVolume = EMPTY_INT  # 可成交数量
        self.closeVolume = EMPTY_INT  # 可成交数量
        # self.maxOpenVolume = EMPTY_INT  # 最大开仓数量
        # self.maxCloseVolume = EMPTY_INT  # 最大平仓数量
        # 最后订单完成时间， 初始化时， 取3天前。
        self.lastOrderCompleted = datetime.datetime.now() - datetime.timedelta(days=3)
        self.lastOrderPlaced = datetime.datetime.now()
        # self.reverseDeposit = 5000000
        # self.marginRates = []
        # self.qtyPerHands = []


	self.timerCount = 0
        self.pending = []
        self.completed = []
        self.triggerQry = 5
        self.trading = False
        self.price1 = {}
        self.price2 = {}
        self.available = 0
        self.pair1 = [{'volume': 0, 'price': 0}, {'volume': 0, 'price': 0}]
        self.pair2 = [{'volume': 0, 'price': 0}, {'volume': 0, 'price': 0}]
        self.spreadPos = {}

        self.ctaEngine.eventEngine.register(EVENT_ACCOUNT, self.onAccountChange)

        for vtSymbol in self.vtSymbols:
            if vtSymbol not in self.spreadPos:
                self.spreadPos[vtSymbol] = 0


    # ----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        if len(self.vtSymbols) != 2:
            self.writeCtaLog('合约数必须为2个')
            raise Exception('合约数必须为2个')
        self.writeCtaLog(u'二腿套利合约下单策略初始化')
        self.pending = []
        self.completed = []
	self.qryCount = 0
        self.trading = False
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'两腿套利合约下单策略启动')
        self.trading = True
        self.timerCount = 0
        # self.lastOrderCompleted = datetime.datetime.now() - datetime.timedelta(days=3)
        self.ctaEngine.eventEngine.register(EVENT_TIMER, self.checkOrder)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.trading = False
        self.ctaEngine.eventEngine.unregister(EVENT_TIMER, self.checkOrder)
        self.writeCtaLog(u'HCRB套利合约下单策略停止')
	self.timerCount = 0
        self.putEvent()

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        if self.inited:
            self.calcPrice('open', tick, self.pair1, self.open)
            self.calcPrice('close', tick, self.pair2, self.close)
            self.putEvent()

    # bid是买价，ask是卖价。
    def calcPrice(self, offset, tick, pair, sendOrderFunc):
        idx = self.vtSymbols.index(tick.symbol) + 1
        direction = self.__getattribute__('direction' + str(idx))

        if offset == 'open' and direction == CTAORDER_BUY:
            priceType = 'ask'
        elif offset == 'open' and direction == CTAORDER_SHORT:
            priceType = 'bid'
        elif offset == 'close' and direction == CTAORDER_BUY:
            priceType = 'bid'
        else:
            priceType = 'ask'

        pair[idx - 1]['price'] = getattr(tick, priceType + 'Price1')
        pair[idx - 1]['volume'] = getattr(tick, priceType + 'Volume1')

        self.__setattr__(offset + 'Spread', pair[0]['price'] - pair[1]['price'])
        volume1 = pair[0]['volume'] / int(self.volumes[0])
        volume2 = pair[1]['volume'] / int(self.volumes[1])
        volume = min(volume1, volume2)
        self.__setattr__(offset + 'Volume', volume)

        spread = self.__getattribute__(offset + 'Spread')
        orderPrice = self.__getattribute__(offset + 'Price')

        if pair[0]['price'] * pair[1]['price']  > 0 \
                and self.__getattribute__(offset + 'Volume') > 1 and self.pending.__len__() == 0 and (
                            (self.direction1 == CTAORDER_BUY and offset == 'open' and spread <= orderPrice)
                        or (self.direction1 == CTAORDER_SHORT and offset == 'open' and spread >= orderPrice)
                    or (self.direction1 == CTAORDER_BUY and offset == 'close' and spread >= orderPrice)
                or (self.direction1 == CTAORDER_SHORT and offset == 'close' and spread <= orderPrice)):
            openC = u'开' if offset == 'open' else '平'
            orderVolume = self.calcAvalVolume(offset, volume, pair)

            # seconds = (datetime.datetime.now() - self.lastOrderCompleted).total_seconds()
            # 上次下单之后，停5秒再下
            # 2017/7/7 不再等5秒下单
            if orderVolume > 0:
                info = u'{}可以{}仓{}组，差价：{}，价格分别是：{},{}'.format(self.vtSymbol, openC, orderVolume, spread,
                                                              pair[0]['price'],
                                                              pair[1]['price'])

                sendOrderFunc(pair[0]['price'], pair[1]['price'], orderVolume)
                self.writeCtaLog(info)
                if self.trading:
                    self.putSmsEvent(info)
            elif orderVolume > 0:
                self.writeCtaLog(
                    u'时间未到，不下单。{}可以{}仓{}组，差价：{}，价格分别是：{},{}'.format(self.vtSymbol, openC, orderVolume, spread,
                                                                       pair[0]['price'],
                                                                       pair[1]['price']))

    # -------------------------------------------------------------------------------------------
    def calcAvalVolume(self, offset, volume, pair):

        if (self.available - self.reverseDeposit)<0:
            self.writeCtaLog('预留保证金后，可用资金不足, 不能开仓. 当前可用资金为{}, 预留{}, 剩余{}'.format(self.available, self.reverseDeposit,
                                                                                 self.available - self.reverseDeposit))
            return 0

        attrOffset = 'maxOpenVolume' if offset == 'open' else 'maxCloseVolume'
        leftVolume = self.__getattribute__(attrOffset)

        if volume / 2 <= leftVolume:
            orderVolume = volume / 2
        else:
            orderVolume = leftVolume

        if orderVolume > self.maxGroupPerTrade:
            orderVolume = self.maxGroupPerTrade
        if offset == 'open':

            unitDeposit = 0
            for i in range(2):
                unitDeposit += pair[i]['price'] * self.marginRates[i] * self.qtyPerHands[i] * self.volumes[i]

            avalVolume = int((self.available - self.reverseDeposit) / unitDeposit)
            avalVolume = 0 if avalVolume < 0 else avalVolume

            if avalVolume < orderVolume:
                self.writeCtaLog('可用资金不足,不能开足仓位.当前可用资金为{}, 开仓{}组所需保证金:{},可开{}组'.format(self.available, orderVolume,
                                                                                       unitDeposit, avalVolume))
            return min(avalVolume, orderVolume)
        else:
            return orderVolume

    @staticmethod
    def price_include_slippage(direction, price, slippage, priceGap):
        if direction == CTAORDER_BUY or direction == CTAORDER_COVER:
            orderPrice = price + slippage * priceGap
        if direction == CTAORDER_SHORT or direction == CTAORDER_SELL:
            orderPrice = price - slippage * priceGap
        return orderPrice

    def buildOrderInfo(self, vtOrderID, vtSymbol, direction, volume, price):
        return {'orderID': vtOrderID,
                'status': STATUS_UNKNOWN,
                'totalVolume': volume,
                'vtOrderID': vtOrderID,
                'tradedVolume': 0,
                'price': price,
                'direction': direction,
                'offset': 0,
                'symbol': vtSymbol,
                'vtSymbol': vtSymbol}

    def open(self, price1, price2, volume):
        if self.trading:
            order1 = self.sendOrder(self.vtSymbols[0], self.direction1, price1, self.slippages[0], self.priceGaps[0],
                                    self.volumes[0] * volume)
            order2 = self.sendOrder(self.vtSymbols[1], self.direction2, price2, self.slippages[1], self.priceGaps[1],
                                    self.volumes[1] * volume)

            order_group = {order1['vtOrderID']: order1, order2['vtOrderID']: order2}
            self.pending.append(order_group)

    def close(self, price1, price2, volume):

        direction1 = CTAORDER_SELL if self.direction1 == CTAORDER_BUY else CTAORDER_COVER
        direction2 = CTAORDER_SELL if self.direction2 == CTAORDER_BUY else CTAORDER_COVER
        direction3 = CTAORDER_SELL if self.direction3 == CTAORDER_BUY else CTAORDER_COVER
        if self.trading:
            order1 = self.sendOrder(self.vtSymbols[0], direction1, price1, self.slippages[0], self.priceGaps[0],
                                    self.volumes[0] * volume)
            order2 = self.sendOrder(self.vtSymbols[1], direction2, price2, self.slippages[1], self.priceGaps[1],
                                    self.volumes[1] * volume)

            order_group = {order1['vtOrderID']: order1, order2['vtOrderID']: order2}
            self.pending.append(order_group)
            # self.eventEngine.register(EVENT_TIMER, self.checkOrder)

    def checkConnection(self, vtSymbol):
        contract = self.ctaEngine.mainEngine.getContract(vtSymbol)
        gateway = self.ctaEngine.mainEngine.getGateway(contract.gatewayName)
        if not gateway.tdConnected or not gateway.mdConnected:
            gateway.connect()

    def sendOrder(self, vtSymbol, direction, price, slippage, priceGap, volume):
        self.checkConnection(vtSymbol)
        orderPrice = self.price_include_slippage(direction, price, slippage, priceGap)
        vtOrderID = self.ctaEngine.sendOrder(vtSymbol, direction, orderPrice, volume, self)
        vtOrderID = vtOrderID.replace('.', '_')
        self.lastOrderPlaced = datetime.datetime.now()
        return self.buildOrderInfo(vtOrderID, vtSymbol, direction, volume, orderPrice)

    # ----------------------------------------------------------------------
    def checkOrder(self, event):
        self.timerCount = self.timerCount + 1
        if self.timerCount < 5:
            return
        self.timerCount = 0
        if self.pending.__len__() > 0:
            seconds = (datetime.datetime.now() - self.lastOrderPlaced).total_seconds()
            if seconds > 5:
                for order_group in self.pending:
                    for order in order_group.values():
                        if order['status'] != STATUS_ALLTRADED and order['status'] != STATUS_CANCELLED:
                            warning = u'当前时间：{} 超过5秒有未完成订单！！{} {}{} @{}, 下单数量:{},已成交数量:{},订单状态:{}'.format(
                                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), order['vtSymbol'],
                                order['offset'],
                                order['direction'],
                                order['price'],
                                order['totalVolume'],
                                order['tradedVolume'],
                                order['status'])
                            self.writeCtaLog(warning)
                            if seconds < 75:
                                self.putSmsEvent(warning)

    def onAccountChange(self, event):
        data = event.dict_['data']
        self.available = data.available
        self.putEvent()

    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""

        pass

    # ----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        vtOrderID = order.vtOrderID.replace('.', '_')
        for order_group in self.pending:
            if vtOrderID in order_group:
                new_status = {'orderID': vtOrderID,
                              'status': order.status,
                              'totalVolume': order.totalVolume,
                              'vtOrderID': vtOrderID,
                              'tradedVolume': order.tradedVolume,
                              'direction': order.direction,
                              'price': order.price,
                              'offset': order.offset,
                              'symbol': order.symbol,
                              'vtSymbol': order.vtSymbol}
                if self.checkChanged(order_group[vtOrderID], new_status):
                    print("------------------------------------")
                    print("old values:")
                    print(order_group[vtOrderID])
                    print("new values:")
                    print(new_status)
                    order_group[vtOrderID] = new_status
                    info = '当前时间:{},订单号:{},合约{}, 方向:{}, 价格:{},状态:{},下单：{}手，成交：{}手'.format(
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), order.orderID, order.vtSymbol,
                        order.direction, order.price, order.status, order.totalVolume,
                        order.tradedVolume)
                    self.writeCtaLog(info)

                    # self.putSmsEvent(info)
                break

        try:
            order_group
        except UnboundLocalError:
            order_group = None

        if order_group is None:
            exit
        if order.status == STATUS_ALLTRADED or order.status == STATUS_CANCELLED:
            group_status = order.status
            for k, v in order_group.items():
                lastOrder = v
                if 'status' not in v:
                    group_status = STATUS_UNKNOWN
                    break
                elif v['status'] != STATUS_ALLTRADED and v['status'] != STATUS_CANCELLED:
                    group_status = v['status']
                    break

            if group_status == STATUS_ALLTRADED or group_status == STATUS_CANCELLED:
                self.completed.append(order_group)
                self.pending.remove(order_group)
                volume = lastOrder['totalVolume'] / self.volumes[self.vtSymbols.index(lastOrder['vtSymbol'])]
                # 记录最后订单完成时间。5秒后， 才能再下第二个，以确保可用金额已回复。
                self.lastOrderCompleted = datetime.datetime.now()
                self.writeCtaLog(
                    '当前交易全部完成！{}'.format(','.join(x['orderID'] for x in order_group.values())))
                if lastOrder['offset'] == OFFSET_OPEN:
                    self.maxOpenVolume -= volume
                else:
                    self.maxCloseVolume -= volume

    def putSmsEvent(self, content):
        sms = SmsEventData()
        sms.smsContent = content
        sms.notifyTo = self.notifyTo
        event = Event(type_=EVENT_CTA_SMS)
        event.dict_['data'] = sms
        self.ctaEngine.eventEngine.put(event)

    # ----------------------------------------------------------------------
    def checkChanged(self, oldValue, newValue):
        '''
        {'orderID': order.orderID,
         'status': order.status,
         'totalVolume': order.totalVolume,
         'vtOrderID': order.vtOrderID,
         'tradedVolume': order.tradedVolume,
         'direction': order.direction,
         'price': order.price,
         'offset': order.offset,
         'symbol': order.symbol,
         'vtSymbol': order.vtSymbol}
        '''
        return not self.compare_dictionaries(oldValue, newValue)

    def compare_dictionaries(self, dict1, dict2):
        if dict1 == None or dict2 == None:
            return False

        if type(dict1) is not dict or type(dict2) is not dict:
            return False

        shared_keys = set(dict2.keys()) & set(dict2.keys())

        if not (len(shared_keys) == len(dict1.keys()) and len(shared_keys) == len(dict2.keys())):
            return False

        dicts_are_equal = True
        for key in dict1.keys():
            if type(dict1[key]) is dict:
                dicts_are_equal = dicts_are_equal and compare_dictionaries(dict1[key], dict2[key])
            else:
                dicts_are_equal = dicts_are_equal and (dict1[key] == dict2[key])

        return dicts_are_equal
    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass

    # -----------------------------------------------------------------------
    def savePosition(self):
        pass

    # -----------------------------------------------------------------------
    def loadPosition(self):
        pass
