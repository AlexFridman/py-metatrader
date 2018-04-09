import datetime
import json
import os
import shutil

from metatrader.backtest import BackTest
from metatrader.mt5 import initizalize

DEPOSIT = 10000
RESULT_DIR = 'D:\\metatrader\\test_res_3'
SYMBOLS_DATA_DIR = 'D:\\metatrader\data'
METATRADER_DIR = 'C:\\Program Files\\MetaTrader 5'


def list_symbols():
    def parse_date(date_str):
        return datetime.datetime.strptime(date_str, '%d%m%Y')

    for file in os.listdir(SYMBOLS_DATA_DIR):
        if file.endswith('.csv'):
            file = file.split('.')[0]
            symbol, _, start_date, end_date = file.split('_')
            start_date, end_date = map(parse_date, (start_date, end_date))

            yield symbol, start_date, end_date


def get_symbol_dates(symbol):
    for s, d1, d2 in list_symbols():
        if s == symbol:
            return d1, d2


def test_strategy(strategy, params, symbol, from_date, to_date, timeframe):
    dir_name = '{}_{}_{}_{}'.format(strategy, timeframe, symbol, datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S'))
    test_dir = os.path.join(RESULT_DIR, dir_name)

    shutil.rmtree(test_dir, ignore_errors=True)
    os.makedirs(test_dir, exist_ok=True)

    def save_conf():
        conf_path = os.path.join(test_dir, 'conf.json')
        with open(conf_path, 'w+') as f:
            json.dump({
                'strategy': strategy,
                'timeframe': timeframe,
                'symbol': symbol,
                'params': params
            }, f)

    strategy_params = {param: {'value': '{0}||{0}||{0}||{0}||Y'.format(value)} for param, value in params.items()}
    backtest = BackTest(test_dir,
                        'Advisors\\{}'.format(strategy),
                        strategy_params,
                        '{}USD'.format(symbol[:3]),
                        timeframe,
                        DEPOSIT,
                        from_date,
                        to_date,
                        shutdown_terminal=False)
    backtest.run()

    save_conf()


if __name__ == '__main__':
    initizalize(METATRADER_DIR)
    params = {'Inp_Signal_MA_Shift': 5, 'Inp_Trailing_MA_Applied': 2, 'Inp_Signal_MA_Method': 3,
              'Inp_Signal_MA_Period': 13, 'Inp_Trailing_MA_Shift': 0, 'Inp_Trailing_MA_Period': 9,
              'Inp_Signal_MA_Applied': 6, 'Inp_Trailing_MA_Method': 1}
    strategy = 'ExpertMAMA'
    symbol = 'DGD'
    timeframe = 'M5'
    start_date, end_date = get_symbol_dates(symbol)
    test_strategy(strategy, params, symbol, start_date, end_date, timeframe)
