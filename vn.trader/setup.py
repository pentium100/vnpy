from cx_Freeze import setup, Executable
packages = []
includefiles = ['ContractData.vt', 'VT_setting.json', 'ctaAlgo/CTA_setting.json',
                'ctaAlgo/CTA_setting2.json', 'dataRecorder/DR_setting.json',
                'riskManager/RM_setting.json', 'ctpGateway/CTP_connect2.json'
                ]
for dbmodule in ['dbhash', 'gdbm', 'dbm', 'dumbdbm']:
    try:
        __import__(dbmodule)
    except ImportError:
        pass
    else:
        # If we found the module, ensure it's copied to the build directory.
        packages.append(dbmodule)


build_exe_options = {'packages': packages, 'include_files':includefiles}
setup(name='vn.trader',
      version='0.1',
      options={"build_exe": build_exe_options},
      description='vnpy trader',
      executables=[Executable("vtMain.py")])