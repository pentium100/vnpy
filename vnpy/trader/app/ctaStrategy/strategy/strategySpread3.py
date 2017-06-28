# encoding: UTF-8

"""
差价交易计算三个合约当前可成交价格的最新差价。
 只做测试用：前两个合约的卖1相加-最后一个合约的买1价
"""


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



