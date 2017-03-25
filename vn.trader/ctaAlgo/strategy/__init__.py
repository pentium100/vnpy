# encoding: UTF-8

'''
动态载入所有的策略类
'''

import os
import importlib
import sys

# 用来保存策略类的字典
STRATEGY_CLASS = {}

# 获取目录路径
if getattr(sys, 'frozen', False):
    # The application is frozen
    datadir = os.path.dirname(sys.executable)
else:
    # The application is not frozen
    # Change this bit to match where you store your data files:
    datadir = os.path.dirname(__file__)

path = os.path.abspath(datadir)

# 遍历strategy目录下的文件
for root, subdirs, files in os.walk(path):
    for name in files:
        # 只有文件名中包含strategy且非.pyc的文件，才是策略文件
        if 'strategy' in name and '.pyc' not in name:
            # 模块名称需要上前缀
            moduleName = 'ctaAlgo.strategy.' + name.replace('.py', '')
            
            # 使用importlib动态载入模块
            module = importlib.import_module(moduleName)
            
            # 遍历模块下的对象，只有名称中包含'Strategy'的才是策略类
            for k in dir(module):
                if 'Strategy' in k:
                    v = module.__getattribute__(k)
                    STRATEGY_CLASS[k] = v
