# encoding: UTF-8


EVENT_CTA_SMS = "eSms"

import json
import os
import requests


class WXNotify:
    settingFileName = 'SMS_setting.json'
    path = os.path.abspath(os.path.dirname(__file__))
    settingFileName = os.path.join(path, settingFileName)

    def __init__(self, eventEngine):
        smsSetting = self.loadSmsSetting()
        self.url = smsSetting['wxUrl']
        self.appId = smsSetting['wxAppId']
        self.secret = smsSetting['wxSecret']

        eventEngine.register(EVENT_CTA_SMS, self.sendSms)
        self.lastMessage = ''


    def loadSmsSetting(self):
        """读取策略配置"""
        with open(self.settingFileName) as f:
            l = json.load(f)
        return l

    # --------------------------------------------------------------------
    def sendSms(self, event):
        sms = event.dict_['data']
        # GET with params in URL
        # print sms.smsContent
        # content = sms.smsContent.decode("utf8")
        # content = content.encode("gbk")
        """
        http://weixin.itg.com.cn/qy/manage/sendmessage?psnid=107030&appid=27&content=测试&password=visa2017
        """
        for notifyTo in sms.notifyToWX:
            payload = {'appid': self.appId, 'password': self.secret, 'content': sms.smsContent, 'psnid': notifyTo}
            requests.post(self.url, data=payload)
            # print r.status_code
            # notifyTo = notifyTo.encode("gbk")
            # cursor = self.myConnection.cursor()
            # print self.myConnection.character_set_name()
            # Read a single record
            # sql = 'insert into api_mt_BBB(mobiles,content,is_wap) values ("%s", "%s", 0)' % (notifyTo, content)
            # sql = sql.decode('latin1')
            # cursor.execute(sql)
