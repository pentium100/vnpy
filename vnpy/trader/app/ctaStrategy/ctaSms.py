# encoding: UTF-8


EVENT_CTA_SMS = "eSms"

import json
import os
import sys
import MySQLdb as mysql
from vnpy.trader.app.ctaStrategy.SmsEventData import SmsEventData

class CtaSms:
    settingFileName = 'SMS_setting.json'
    path = os.path.abspath(os.path.dirname(__file__))
    settingFileName = os.path.join(path, settingFileName)

    def __init__(self, eventEngine):
        smsSetting = self.loadSmsSetting()
        self.hostname = smsSetting['hostname']
        self.username = smsSetting['username']
        self.password = smsSetting['password']
        self.database = smsSetting['database']
        self.myConnection = None
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

        self.myConnection = mysql.connect(host=self.hostname, user=self.username, passwd=self.password, db=self.database)
        self.myConnection.autocommit(True)

    def checkDBConnected(self):
        sq = "SELECT NOW()"
        try:
            cursor = self.myConnection.cursor()
            cursor.execute(sq)
        except mysql.Error as e:
            if e.errno == 2006:
                return self.connectToDB()
            else:
                print ("No connection with database.")
                return False

    def sendSms(self, event):
        sms = event.dict_['data']
        print sms.smsContent
        content = sms.smsContent.decode("utf8")
        content = content.encode("gbk")
        try:
            if not self.checkDBConnected():
                self.connectToDB()

            for notifyTo in sms.notifyTo:
                notifyTo = notifyTo.encode("gbk")
                cursor = self.myConnection.cursor()
                print self.myConnection.character_set_name()
                # Read a single record
                sql = 'insert into api_mt_BBB(mobiles,content,is_wap) values ("%s", "%s", 0)' % (notifyTo, content)
                # sql = sql.decode('latin1')
                cursor.execute(sql)
        except:
            e = sys.exc_info()[0]
            print e
