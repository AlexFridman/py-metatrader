from datetime import datetime

from metatrader.backtest import BackTest
from metatrader.mt5 import initizalize


def main():
    initizalize('C:\\Program Files\\MetaTrader 5')

    from_date = datetime(2017, 9, 1)
    to_date = datetime(2018, 1, 1)

    ea_name = 'Examples\\MACD\\MACD Sample'
    conf_dir = 'D:\\metatrader'
    backtest = BackTest(conf_dir, ea_name, {}, 'USDJPY', 'M5', 10000, from_date, to_date)
    ret = backtest.run()


if __name__ == '__main__':
    main()
