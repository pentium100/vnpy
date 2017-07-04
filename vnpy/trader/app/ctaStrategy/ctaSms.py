# encoding: UTF-8


EVENT_CTA_SMS = "eSms"

import json
import os
import MySQLdb as mysql
from vnpy.trader.app.ctaStrategy.SmsEventData import SmsEventData

class CtaSms:
    settingFileName = 'SMS_setting.json'
    path = os.path.abspath(os.path.dirname(__file__))
    settingFileName = os.path.join(path, settingFileName)

    def __init__(self, eventEngine):
        self.connectToDB()
        eventEngine.register(EVENT_CTA_SMS, self.sendSms)
        self.lastSms = ''


    def loadSmsSetting(self):
        """读取策略配置"""
        with open(self.settingFileName) as f:
            l = json.load(f)
        return l


    # --------------------------------------------------------------------
    def connectToDB(self):
        smsSetting = self.loadSmsSetting()
        hostname = smsSetting['hostname']
        username = smsSetting['username']
        password = smsSetting['password']
        database = smsSetting['database']
        self.myConnection = mysql.connect(host=hostname, user=username, passwd=password, db=database)
        self.myConnection.autocommit(True)



    def sendSms(self, event):
        sms = event.dict_['data']

        content = sms.smsContent.decode("utf8")
        content = content.encode("gbk")

        for notifyTo in sms.notifyTo:
            notifyTo = notifyTo.encode("gbk")
            cursor = self.myConnection.cursor()
            print self.myConnection.character_set_name()
            # Read a single record
            sql = 'insert into api_mt_BBB(mobiles,content,is_wap) values ("%s", "%s", 0)' % (notifyTo, content)
            # sql = sql.decode('latin1')
            cursor.execute(sql)
