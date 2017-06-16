# encoding: UTF-8

"""
用于vn.trader的运行目录环境设置
"""

import os
import sys

# 将根目录路径添加到环境变量中
if getattr(sys, 'frozen', False):
    # The application is frozen
    datadir = os.path.dirname(sys.executable)
else:
    # The application is not frozen
    # Change this bit to match where you store your data files:
    datadir = os.path.dirname(__file__)
ROOT_PATH = os.path.abspath(datadir)
sys.path.insert(0, '.\\language')
sys.path.append(ROOT_PATH)

# 将功能模块的目录路径添加到环境变量中
# 若各目录下存在同名文件可能导致异常，请注意测试
MODULE_PATH = {}
MODULE_PATH['CTA'] = os.path.join(ROOT_PATH, 'ctaStrategy')
MODULE_PATH['RM'] = os.path.join(ROOT_PATH, 'riskManager')
MODULE_PATH['DR'] = os.path.join(ROOT_PATH, 'dataRecorder')

# 添加到环境变量中
for path in MODULE_PATH.values():
    if path not in sys.path:
        sys.path.append(path)
