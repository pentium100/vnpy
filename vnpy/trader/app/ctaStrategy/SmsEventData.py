# encoding: UTF-8

from vnpy.trader.vtObject import VtBaseData
import time
from vnpy.trader.vtConstant import (EMPTY_STRING, EMPTY_UNICODE,
                                    EMPTY_FLOAT, EMPTY_INT)

class SmsEventData(VtBaseData):
    """短消息数据类"""

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(SmsEventData, self).__init__()

        self.smsTime = time.strftime('%X', time.localtime())  # 日志生成时间
        self.smsContent = EMPTY_UNICODE  # 日志信息
        self.notifyTo = []
        self.notifyToWX = []
