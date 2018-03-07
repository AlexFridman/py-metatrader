# -*- coding: utf-8 -*-
'''
Created on 2015/01/25

@author: samuraitaiga
'''
import os
import shutil
from itertools import chain

from metatrader.mt5 import DEFAULT_MT5_NAME
from metatrader.mt5 import get_mt5


class BackTest:
    """
    Attributes:
      ea_name(string): ea name
      param(dict): ea parameter
      symbol(string): currency symbol. e.g.: USDJPY
      from_date(datetime.datetime): backtest from date
      to_date(datetime.datetime): backtest to date
      model(int): backtest model 
        0: Every tick
        1: Control points
        2: Open prices only
      spread(int): spread
      optimization(bool): optimization flag. optimization is enabled if True
      replace_report(bool): replace report flag. replace report is enabled if True

    """

    def __init__(self, test_dir, ea_name, param, symbol, period, deposit, from_date, to_date, model=1, spread=5,
                 forward_mode=0, execution_mode=1, replace_report=True, leverage='1:100', shutdown_terminal=True):
        self.test_dir = test_dir
        self.ea_name = ea_name
        self.param = param
        self.symbol = symbol
        self.period = period
        self.forward_mode = forward_mode
        self.execution_mode = execution_mode
        self.deposit = deposit
        self.from_date = from_date
        self.to_date = to_date
        self.model = model
        self.spread = spread
        self.replace_report = replace_report
        self.leverage = leverage
        self.shutdown_terminal = shutdown_terminal

    def _prepare(self, alias=DEFAULT_MT5_NAME):
        """
        Notes:
          create backtest config file and parameter file
        """
        self._create_conf(alias=alias)
        self._create_param(alias=alias)

    def _create_conf(self, alias=DEFAULT_MT5_NAME):
        """
        Notes:
          create config file(.conf) which is used parameter of terminal64.exe
          in %APPDATA%\\MetaQuotes\\Terminal\\<UUID>\\tester
          
          file contents goes to 
            TestExpert=SampleEA
            TestExpertParameters=SampleEA.set
            TestSymbol=USDJPY
            TestPeriod=M5
            TestModel=0
            TestSpread=5
            TestOptimization=true
            TestDateEnable=true
            TestFromDate=2014.09.01
            TestToDate=2015.01.05
            TestReport=SampleEA
            TestReplaceReport=false
            TestShutdownTerminal=true
        """

        mt5 = get_mt5(alias)
        conf_file = os.path.join(self.test_dir, 'config.ini')
        report_dir = os.path.join(mt5.appdata_path, 'report')
        os.makedirs(report_dir, exist_ok=True)

        with open(conf_file, 'w+') as fp:
            fp.write('[Tester]\n')
            fp.write('Expert=%s\n' % self.ea_name)
            fp.write('ExpertParameters=%s\n' % 'param.set')
            fp.write('Symbol=%s\n' % self.symbol)
            fp.write('Model=%s\n' % self.model)
            fp.write('Deposit=%s\n' % self.deposit)
            fp.write('ForwardMode=%s\n' % self.forward_mode)
            fp.write('ExecutionMode=%s\n' % self.execution_mode)
            fp.write('Period=%s\n' % self.period)
            fp.write('FromDate=%s\n' % self.from_date.strftime('%Y.%m.%d'))
            fp.write('ToDate=%s\n' % self.to_date.strftime('%Y.%m.%d'))
            fp.write('Report=%s\n' % 'report/report')
            fp.write('Leverage=%s\n' % self.leverage)
            fp.write('ReplaceReport=%s\n' % int(self.replace_report))
            fp.write('ShutdownTerminal=%s\n' % int(self.shutdown_terminal))

    def _create_param(self, alias=DEFAULT_MT5_NAME):
        """
        Notes:
          create ea parameter file(.set) in %APPDATA%\\MetaQuotes\\Terminal\\<UUID>\\tester
        Args:
          ea_name(string): ea name
        """
        param_file = os.path.join(self.test_dir, 'param.set')
        param = chain.from_iterable((self.param.items(), (('Inp_Expert_Title', {'value': self.ea_name}),)))

        with open(param_file, 'w+') as fp:
            for k, values in param:
                values = values.copy()
                value = values.pop('value')
                fp.write('%s=%s\n' % (k, value))
                if self.optimization:
                    if values.has_key('max') and values.has_key('interval'):
                        fp.write('%s,F=1\n' % k)
                        fp.write('%s,1=%s\n' % (k, value))
                        interval = values.pop('interval')
                        fp.write('%s,2=%s\n' % (k, interval))
                        maximum = values.pop('max')
                        fp.write('%s,3=%s\n' % (k, maximum))
                    else:
                        # if this value won't be optimized, write unused dummy data for same format.
                        fp.write('%s,F=0\n' % k)
                        fp.write('%s,1=0\n' % k)
                        fp.write('%s,2=0\n' % k)
                        fp.write('%s,3=0\n' % k)
                else:
                    if type(value) == str:
                        # this ea arg is string. then don't write F,1,2,3 section in config
                        pass
                    else:
                        # write unused dummy data for same format.
                        fp.write('%s,F=0\n' % k)
                        fp.write('%s,1=0\n' % k)
                        fp.write('%s,2=0\n' % k)
                        fp.write('%s,3=0\n' % k)

        mt5 = get_mt5(alias)
        real_param_path = os.path.join(mt5.appdata_path, 'MQL5\\Profiles\\Tester', 'param.set')
        shutil.copy(param_file, real_param_path)

    def _get_conf_abs_path(self, alias=DEFAULT_MT5_NAME):
        conf_file = os.path.join(self.test_dir, 'config.ini')
        return conf_file

    def move_and_fix_report(self, alias=DEFAULT_MT5_NAME):
        mt5 = get_mt5(alias)
        src_report_dir = os.path.join(mt5.appdata_path, 'report')
        dst_report_dir = os.path.join(self.test_dir, 'report')
        shutil.rmtree(dst_report_dir, ignore_errors=True)
        shutil.move(src_report_dir, self.test_dir)
        content_dir = os.path.join(dst_report_dir, 'report')
        os.makedirs(content_dir)

        for file_name in os.listdir(dst_report_dir):
            if file_name.endswith('.png'):
                src_file_path = os.path.join(dst_report_dir, file_name)
                dst_file_path = os.path.join(content_dir, file_name)
                shutil.move(src_file_path, dst_file_path)

    def run(self, alias=DEFAULT_MT5_NAME):
        """
        Notes:
          run backtest
        """

        self.optimization = False

        self._prepare(alias=alias)
        bt_conf = self._get_conf_abs_path(alias=alias)

        mt5 = get_mt5(alias=alias)
        mt5.run(conf=bt_conf)
        self.move_and_fix_report()

    def optimize(self, alias=DEFAULT_MT5_NAME):
        """
        """
        from metatrader.report import OptimizationReport

        self.optimization = True
        self._prepare(alias=alias)
        bt_conf = self._get_conf_abs_path(alias=alias)

        mt5 = get_mt5(alias=alias)
        mt5.run(conf=bt_conf)

        ret = OptimizationReport(self)
        return ret
