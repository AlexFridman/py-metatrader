import os
import shutil
from datetime import datetime

from sklearn.model_selection import ParameterGrid

from metatrader.backtest import BackTest
from metatrader.mt5 import initizalize

CONF_FILE_PATH = 'D:\\metatrader\config.ini'
PARAM_FILE_PATH = 'D:\\metatrader\param.set'
DATA_DIR = 'D:\\metatrader\data'


def prepare_dir(prefix, name):
    path = os.path.join(prefix, name)

    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)
    return path


def list_symbols():
    def parse_darte(date_str):
        return datetime.strptime(date_str, '%d%m%Y')

    for file in os.listdir(DATA_DIR):
        if file.endswith('.csv'):
            file = file.split('.')[0]
            symbol, _, start_date, end_date = file.split('_')
            start_date, end_date = map(parse_darte, (start_date, end_date))

            if 'CND' in symbol:
                yield symbol, start_date, end_date


def main():
    initizalize('C:\\Program Files\\MetaTrader 5')
    ea_name = 'Advisors\\ExpertMACD'
    param_space = {
        'timeframe': ['M1', 'M5', 'M15', 'H1', 'H4'],
        'Inp_Signal_MACD_PeriodFast': [5, 8, 13, 21, 34, 55],
        'Inp_Signal_MACD_PeriodSlow': [5, 8, 13, 21, 34, 55]
    }
    reports_dir = r'D:\\metatrader\reports'
    shutil.rmtree(reports_dir, ignore_errors=True)

    for symbol, from_date, to_date in list_symbols():
        symbol_reports_dir = os.path.join(reports_dir, symbol)
        os.makedirs(symbol_reports_dir, exist_ok=True)

        for i, params in enumerate(ParameterGrid(param_space)):
            if not (params['Inp_Signal_MACD_PeriodFast'] == 5 and params['Inp_Signal_MACD_PeriodSlow'] == 8):
                continue

            config_dir = prepare_dir(symbol_reports_dir, '{0:03d}'.format(i))
            print('Tesing', symbol, i)
            advisor_params = {
                'Inp_Signal_MACD_PeriodFast': {
                    'value': '{0}||{0}||1||120||Y'.format(params['Inp_Signal_MACD_PeriodFast'])
                },
                'Inp_Signal_MACD_PeriodSlow': {
                    'value': '{0}||{0}||1||240||Y'.format(params['Inp_Signal_MACD_PeriodSlow'])
                },
                'Inp_Expert_Title': {'value': 'ExpertMACD'}
            }
            backtest = BackTest(config_dir, ea_name, advisor_params,
                                '{}USD'.format(symbol), params['timeframe'],
                                10000, from_date, to_date)
            backtest.run()


if __name__ == '__main__':
    main()
