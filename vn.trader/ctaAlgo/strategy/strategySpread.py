# encoding: UTF-8

"""
差价交易计算三个合约当前可成交价格的最新差价。
 只做测试用：前两个合约的卖1相加-最后一个合约的买1价
"""

from ctaBase import *
from ctaTemplate import CtaTemplate


########################################################################
class SpreadStrategy(CtaTemplate):
    """三合约价差计算Demo"""
    className = 'SpreadCalcDemo'
    author = u'clw@itg'

    # 策略参数
    contract1 = 'short'  # 合约1方向
    contract2 = 'long'  # 合约2方向
    contract3 = 'long'  #合约3方向

    # 策略变量
    price1 = EMPTY_FLOAT  # 合约1最新可成交价
    price2 = EMPTY_FLOAT  # 合约2最新可成交价
    price3 = EMPTY_FLOAT  # 合约3最新可成交价
    volume1 = EMPTY_INT  # 可成交数量
    volume2 = EMPTY_INT  # 可成交数量
    volume3 = EMPTY_INT  # 可成交数量
    spread = EMPTY_FLOAT  # 最新可成交差价
    volume = EMPTY_INT  # 可成交数量

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'contract1',
                 'contract2',
                 'contract3'
                 ]

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'price1',
               'price2',
               'price3',
               'spread',
               'volume'
               ]

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(SpreadStrategy, self).__init__(ctaEngine, setting)
        self.vtSymbols = setting['vtSymbol'].split(u',')



    # ----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        if len(self.vtSymbols) != 3:
            self.writeCtaLog('合约数必须为3个')
            raise Exception('合约数必须为3个')
        self.writeCtaLog(u'Spread Calc演示策略初始化')
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'Spread Calc演示策略启动')
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'Spread Calc演示策略停止')
        self.putEvent()

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""

        idx = self.vtSymbols.index(tick.symbol)+1
        direction = 'ask' if getattr(self, 'contract'+str(idx)) == 'long' else 'bid'
        setattr(self, 'price' + str(idx), getattr(tick, direction + 'Price1'))
        setattr(self, 'volume' + str(idx), getattr(tick, direction + 'Volume1'))
        self.spread = self.price1 - 1.5*self.price2 - 0.5*self.price3 - 900

        self.volume = min(self.volume1, self.volume2, self.volume3)
        self.putEvent()



    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        pass

    # ----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""

        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass

    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass

