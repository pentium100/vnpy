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
from strategySpread import SpreadStrategy


########################################################################
class SpreadStrategy3(SpreadStrategy):
    """三合约价差计算Demo"""
    className = 'SpreadCalcDemo3'

    author = u'clw@itg'


    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(SpreadStrategy3, self).__init__(ctaEngine, setting)

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

        self.__setattr__(offset + 'Spread', pair[0]['price'] - 1.5 * pair[1]['price'] - 0.55 * pair[2]['price'] - 800)
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
