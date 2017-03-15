# encoding: UTF-8

"""
差价交易计算三个合约当前可成交价格的最新差价。
 只做测试用：前两个合约的卖1相加-最后一个合约的买1价
"""

from ctaBase import *
from vtConstant import *
import datetime
from eventType import *
from ctaTemplate import CtaTemplate


########################################################################
class SpreadStrategy(CtaTemplate):
    """三合约价差计算Demo"""
    className = 'SpreadCalcDemo'
    author = u'clw@itg'

    # 策略参数
    direction1 = CTAORDER_SHORT  # 合约1方向
    direction2 = CTAORDER_BUY  # 合约2方向
    direction3 = CTAORDER_BUY  # 合约3方向
    unitDeposit = EMPTY_FLOAT  # 每组所需的保证金

    # 策略变量
    price1 = EMPTY_FLOAT  # 合约1最新可成交价
    price2 = EMPTY_FLOAT  # 合约2最新可成交价
    price3 = EMPTY_FLOAT  # 合约3最新可成交价
    volume1 = EMPTY_INT  # 可成交数量
    volume2 = EMPTY_INT  # 可成交数量
    volume3 = EMPTY_INT  # 可成交数量
    openSpread = EMPTY_FLOAT  # 最新可成交差价
    closeSpread = EMPTY_FLOAT  # 最新可成交差价
    openVolume = EMPTY_INT  # 可成交数量
    closeVolume = EMPTY_INT  # 可成交数量
    maxOpenVolume = EMPTY_INT  # 最大持仓组
    maxCloseVolume = EMPTY_INT  # 最大持仓组
    lastOrderCompleted = datetime.datetime.now() - datetime.timedelta(days=3)  # 最后订单完成时间， 初始化时， 取3天前。
    lastOrderPlaced = datetime.datetime.now()
    marginRates = []
    qtyPerHands = []
    reverseDeposit = 5000000

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'vtSymbol',
                 'volumes',
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
    qryCount = 0
    pair1 = [{'volume': 0, 'price': 0}, {'volume': 0, 'price': 0}, {'volume': 0, 'price': 0}]
    pair2 = [{'volume': 0, 'price': 0}, {'volume': 0, 'price': 0}, {'volume': 0, 'price': 0}]

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(SpreadStrategy, self).__init__(ctaEngine, setting)
        self.vtSymbols = setting['vtSymbol'].split(u',')

        self.pending = []
        self.completed = []
        self.triggerQry = 5
        self.trading = False
        self.price1 = {}
        self.price2 = {}
        self.available = 0

        self.ctaEngine.eventEngine.register(EVENT_ACCOUNT, self.onAccountChange)

        for vtSymbol in self.vtSymbols:
            if vtSymbol not in self.spreadPos:
                self.spreadPos[vtSymbol] = 0

        '''
        self.volumes = setting['volumes'].split(u',')
        self.slippages = setting['slippages'].split(u',')
        self.priceGaps = setting['priceGaps'].split(u',')
        '''

    # ----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        if len(self.vtSymbols) != 3:
            self.writeCtaLog('合约数必须为3个')
            raise Exception('合约数必须为3个')
        self.writeCtaLog(u'Spread Calc演示策略初始化')
        self.pending = []
        self.completed = []
        self.qryCount = 0
        self.trading = False
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'Spread Calc演示策略启动')
        self.trading = True
        # self.lastOrderCompleted = datetime.datetime.now() - datetime.timedelta(days=3)
        self.ctaEngine.eventEngine.register(EVENT_TIMER, self.checkOrder)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.trading = False
        self.ctaEngine.eventEngine.unregister(EVENT_TIMER, self.checkOrder)
        self.writeCtaLog(u'Spread Calc演示策略停止')
        self.putEvent()

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        # if self.inited:
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

        self.__setattr__(offset + 'Spread', pair[0]['price'] - 1.5 * pair[1]['price'] - 0.5 * pair[2]['price'] - 900)
        volume1 = pair[0]['volume'] / int(self.volumes[0])
        volume2 = pair[1]['volume'] / int(self.volumes[1])
        volume3 = pair[2]['volume'] / int(self.volumes[2])
        volume = min(volume1, volume2, volume3)
        self.__setattr__(offset + 'Volume', volume)

        spread = self.__getattribute__(offset + 'Spread')
        orderPrice = self.__getattribute__(offset + 'Price')

        if pair[0]['price'] * pair[1]['price'] * pair[2]['price'] > 0 \
                and self.__getattribute__(offset + 'Volume') > 1 and self.pending.__len__() == 0 and (
                            (self.direction1 == CTAORDER_BUY and offset == 'open' and spread <= orderPrice)
                        or (self.direction1 == CTAORDER_SHORT and offset == 'open' and spread >= orderPrice)
                    or (self.direction1 == CTAORDER_BUY and offset == 'close' and spread >= orderPrice)
                or (self.direction1 == CTAORDER_SHORT and offset == 'close' and spread <= orderPrice)):
            openC = u'开' if offset == 'open' else '平'
            orderVolume = self.calcAvalVolume(offset, volume, pair)

            seconds = (datetime.datetime.now() - self.lastOrderCompleted).total_seconds()
            # 上次下单之后，停5秒再下
            if orderVolume > 0 and seconds > 5:
                self.writeCtaLog(
                    u'{}可以{}仓{}组，差价：{}，价格分别是：{},{},{}'.format(self.vtSymbol, openC, orderVolume, spread,
                                                              pair[0]['price'],
                                                              pair[1]['price'],
                                                              pair[2]['price']))
                sendOrderFunc(pair[0]['price'], pair[1]['price'], pair[2]['price'], orderVolume)
            elif orderVolume > 0:
                self.writeCtaLog(
                    u'时间未到，不下单。{}可以{}仓{}组，差价：{}，价格分别是：{},{},{}'.format(self.vtSymbol, openC, orderVolume, spread,
                                                                       pair[0]['price'],
                                                                       pair[1]['price'],
                                                                       pair[2]['price']))

    # -------------------------------------------------------------------------------------------
    def calcAvalVolume(self, offset, volume, pair):

        attrOffset = 'maxOpenVolume' if offset == 'open' else 'maxCloseVolume'
        leftVolume = self.__getattribute__(attrOffset)

        if volume / 2 <= leftVolume:
            orderVolume = volume / 2
        else:
            orderVolume = leftVolume

        if offset == 'open':

            unitDeposit = 0
            for i in range(3):
                unitDeposit += pair[i]['price'] * self.marginRates[i] * self.qtyPerHands[i] * self.volumes[i]

            avalVolume = int((self.available - self.reverseDeposit) / unitDeposit)

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
        return {'orderID': 0,
                'status': STATUS_UNKNOWN,
                'totalVolume': volume,
                'vtOrderID': vtOrderID,
                'tradedVolume': 0,
                'price': price,
                'direction': direction,
                'offset': 0,
                'symbol': '',
                'vtSymbol': vtSymbol}

    def open(self, price1, price2, price3, volume):
        if self.trading:
            order1 = self.sendOrder(self.vtSymbols[0], self.direction1, price1, self.slippages[0], self.priceGaps[0],
                                    self.volumes[0] * volume)
            order2 = self.sendOrder(self.vtSymbols[1], self.direction2, price2, self.slippages[1], self.priceGaps[1],
                                    self.volumes[1] * volume)
            order3 = self.sendOrder(self.vtSymbols[2], self.direction3, price3, self.slippages[2], self.priceGaps[2],
                                    self.volumes[2] * volume)
            order_group = {order1['vtOrderID']: order1, order2['vtOrderID']: order2, order3['vtOrderID']: order3}
            self.pending.append(order_group)

    def close(self, price1, price2, price3, volume):

        direction1 = CTAORDER_SELL if self.direction1 == CTAORDER_BUY else CTAORDER_COVER
        direction2 = CTAORDER_SELL if self.direction2 == CTAORDER_BUY else CTAORDER_COVER
        direction3 = CTAORDER_SELL if self.direction3 == CTAORDER_BUY else CTAORDER_COVER
        if self.trading:
            order1 = self.sendOrder(self.vtSymbols[0], direction1, price1, self.slippages[0], self.priceGaps[0],
                                    self.volumes[0] * volume)
            order2 = self.sendOrder(self.vtSymbols[1], direction2, price2, self.slippages[1], self.priceGaps[1],
                                    self.volumes[1] * volume)
            order3 = self.sendOrder(self.vtSymbols[2], direction3, price3, self.slippages[2], self.priceGaps[2],
                                    self.volumes[2] * volume)
            order_group = {order1['vtOrderID']: order1, order2['vtOrderID']: order2, order3['vtOrderID']: order3}
            self.pending.append(order_group)
            # self.eventEngine.register(EVENT_TIMER, self.checkOrder)

    def sendOrder(self, vtSymbol, direction, price, slippage, priceGap, volume):
        orderPrice = self.price_include_slippage(direction, price, slippage, priceGap)
        vtOrderID = self.ctaEngine.sendOrder(vtSymbol, direction, orderPrice, volume, self)
        vtOrderID = vtOrderID.replace('.', '_')
        self.lastOrderPlaced = datetime.datetime.now()
        return self.buildOrderInfo(vtOrderID, vtSymbol, direction, volume, price)

    # ----------------------------------------------------------------------
    def checkOrder(self, event):
        if self.pending.__len__() > 0:
            seconds = (datetime.datetime.now() - self.lastOrderPlaced).total_seconds()
            if seconds > 5:
                for order_group in self.pending:
                    for order in order_group.values():
                        if order['status'] != STATUS_ALLTRADED and order['status'] != STATUS_CANCELLED:
                            self.writeCtaLog(
                                u'超过5秒有未完成订单！！{} {} @{}, 下单数量:{},已成交数量:{}'.format(order['vtSymbol'],
                                                                                     order['direction'], order['price'],
                                                                                     order['totalVolume'],
                                                                                     order['tradedVolume']))

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
                order_group[vtOrderID] = {'orderID': order.orderID,
                                          'status': order.status,
                                          'totalVolume': order.totalVolume,
                                          'vtOrderID': order.vtOrderID,
                                          'tradedVolume': order.tradedVolume,
                                          'direction': order.direction,
                                          'price': order.price,
                                          'offset': order.offset,
                                          'symbol': order.symbol,
                                          'vtSymbol': order.vtSymbol}
                self.writeCtaLog('订单号:{},状态:{},下单：{}手，成交：{}手'.format(order.orderID, order.status, order.totalVolume,
                                                                     order.tradedVolume))
                break

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
