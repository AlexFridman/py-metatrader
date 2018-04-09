import datetime
import json
import os
import shutil

from sklearn.model_selection import ParameterSampler

from metatrader.backtest import BackTest
from metatrader.mt5 import initizalize

SYMBOLS_DATA_DIR = 'D:\\metatrader\data'
RESULT_DIR = 'D:\\metatrader\\test_res_2'
TIMEFRAMES = ['M5', 'H1', 'M15', 'M30']
METATRADER_DIR = 'C:\\Program Files\\MetaTrader 5'
DEPOSIT = 10000
N_PARAM_COMBS = 50


def gen_param_dist(x, t=float, precision=2):
    scalers = [-0.2, -0.1, 0, 0.1, 0.2]
    values = list(map(t, [x * (1 + s) for s in scalers]))
    if t is float:
        return [round(v, 2) for v in values]
    return values


TEST_CONFIG = {
    'Expert_iccl_ima': {
        'Inp_CCI_ma_period': gen_param_dist(14, int),
        'Inp_CCI_close_ma_period': gen_param_dist(14, int),
        'Inp_MA_ma_period': gen_param_dist(9, int),
        'InpMM': ['false'],
        'InpLots': gen_param_dist(0.1, float),
        'InpStopLoss': gen_param_dist(50, int),
        'InpTakeProfit': gen_param_dist(40, int),
    },
    'ExpertMAMA': {
        'Inp_Signal_MA_Period': gen_param_dist(12, int),
        'Inp_Signal_MA_Shift': gen_param_dist(6, int),
        'Inp_Signal_MA_Method': [0, 1, 2, 3],
        'Inp_Signal_MA_Applied': [1, 2, 3, 4, 5, 6, 7],
        'Inp_Trailing_MA_Period': gen_param_dist(12, int),
        'Inp_Trailing_MA_Shift': [0, 2, 4, 6, 8],
        'Inp_Trailing_MA_Method': [0, 1, 2, 3],
        'Inp_Trailing_MA_Applied': [1, 2, 3, 4, 5, 6, 7],
    },
    'MAMACD': {
        'MA1': gen_param_dist(90, int),
        'MA2': gen_param_dist(75, int),
        'MA3': gen_param_dist(5, int),
        'fastema': gen_param_dist(15, int),
        'slowema': gen_param_dist(26, int),
        'InpLots': gen_param_dist(0.1, float),
        'InpStopLoss': gen_param_dist(15, int),
        'InpTakeProfit': gen_param_dist(15, int),
    },
    'N_Candles_v5': {
        'InpN_candles': gen_param_dist(3, int),
        'InpLot': gen_param_dist(0.01, float),
        'InpTakeProfit': gen_param_dist(50, int),
        'InpStopLoss': gen_param_dist(50, int),
        'InpTrailingStop': gen_param_dist(10, int),
        'InpTrailingStep': gen_param_dist(4, int),
        'InpMaxPositions': gen_param_dist(2, int),
        'InpMaxPositionVolume': gen_param_dist(2, float),
        'InpUseTradeHours': ['true', 'false'],
        'InpStartHour': [0],
        'InpEndHour': [23],
        'm_slippage': gen_param_dist(30, int)
    },
    # '3MACross': {
    #     'InpLots': gen_param_dist(0.1, float),
    #     'InpStopLoss': [0, 2, 4, 6, 8, 10],
    #     'InpTakeProfit': gen_param_dist(145, int),
    #     'InpTrailingStop': [0, 2, 4, 6, 8, 10],
    #     'Risk': gen_param_dist(10, float),
    #     'InpAutoSLTP': ['true', 'false'],
    #     'InpTradeAtCloseBar': ['true', 'false'],
    #     'crossesOnCurrent': ['true', 'false'],
    #     'alertsOn': ['false'],
    #     'alertsMessage': ['false'],
    #     'alertsSound': ['false'],
    #     'alertsEmail': ['false'],
    #     'InpBreakEven': gen_param_dist(15, int),
    #     'InpMaxOpenPositions': gen_param_dist(5, int),
    #     'InpMAPeriodFirst': gen_param_dist(23, int),
    #     'InpMAShiftFirst': [0, 2, 4, 6, 8, 10],
    #     'InpMAMethodFirst': [0, 1, 2, 3],
    #     'InpMAPeriodSecond': gen_param_dist(61, int),
    #     'InpMAShiftSecond': [0, 2, 4, 6, 8, 10],
    #     'InpMAMethodSecond': [0, 1, 2, 3],
    #     'InpMAPeriodThird': gen_param_dist(122, int),
    #     'InpMAShiftThird': [0, 2, 4, 6, 8, 10],
    #     'InpMAMethodThird': [0, 1, 2, 3],
    #     'InpChannelPeriod': gen_param_dist(15, int)
    #
    # }
}


def dict_to_set(d):
    return frozenset(d.items())


def load_already_tested_configurations():
    confs = set()

    if not os.path.exists(RESULT_DIR):
        return confs

    for folder in os.listdir(RESULT_DIR):
        path = os.path.join(RESULT_DIR, folder, 'conf.json')
        if os.path.exists(path):
            with open(path) as f:
                conf = json.load(f)
                confs.add((conf['strategy'], dict_to_set(conf['params']), conf['symbol'], conf['timeframe']))
    return confs


def list_symbols():
    def parse_date(date_str):
        return datetime.datetime.strptime(date_str, '%d%m%Y')

    for file in os.listdir(SYMBOLS_DATA_DIR):
        if file.endswith('.csv'):
            file = file.split('.')[0]
            symbol, _, start_date, end_date = file.split('_')
            start_date, end_date = map(parse_date, (start_date, end_date))

            yield symbol, start_date, end_date


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
                        to_date)
    backtest.run()

    save_conf()


def run_testing(already_tested_configurations, test_config):
    n_tested, n_skipped = 0, len(already_tested_configurations)
    symbols = list(list_symbols())
    total = len(test_config) * len(TIMEFRAMES) * len(symbols) * N_PARAM_COMBS

    for strategy, param_space in sorted(test_config.items()):
        for params in ParameterSampler(param_space, N_PARAM_COMBS, random_state=1):
            for timeframe in TIMEFRAMES:
                for (symbol, from_date, to_date) in symbols:
                    if (strategy, dict_to_set(params), symbol, timeframe) not in already_tested_configurations:
                        test_strategy(strategy, params, symbol, from_date, to_date, timeframe)
                        n_tested += 1
                        print('skipped:', n_skipped, 'tested:', n_tested, n_skipped + n_tested, '/', total)
                    else:
                        n_skipped += 1


def main():
    initizalize(METATRADER_DIR)
    run_testing(load_already_tested_configurations(), TEST_CONFIG)


if __name__ == '__main__':
    main()
