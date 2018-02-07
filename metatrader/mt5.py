# -*- coding: utf-8 -*-
"""
@author: samuraitaiga
"""
import logging
import os

_mt5s = {}

DEFAULT_MT5_NAME = 'default'
# mt4 program file path is written in origin.txt 
ORIGIN_TXT = 'origin.txt'


class MT5(object):
    """
    Notes:
      meta trader5 class which can lunch metatrader5.
      this class will only lunch metatrader5,
      because metatrader5 can lunch either normal mode or backtest mode.
    """
    prog_path = None
    appdata_path = None

    def __init__(self, prog_path):
        if os.path.exists(prog_path):
            self.prog_path = prog_path
            if is_uac_enabled():
                self.appdata_path = get_appdata_path(prog_path)
            else:
                self.appdata_path = prog_path

        else:
            err_msg = 'prog_path %s not exists' % prog_path
            logging.error(err_msg)
            raise IOError(err_msg)

        self.mt_exe = self.get_mt5_exe_file_name(self.prog_path)

    @staticmethod
    def get_mt5_exe_file_name(prog_path):
        file_names = set(map(str.lower, os.listdir(prog_path)))
        if 'terminal.exe' in file_names:
            return 'terminal.exe'
        elif 'terminal64.exe' in file_names:
            return 'terminal64.exe'
        raise FileNotFoundError('terminal.exe not found')

    def run(self, conf=None):
        """
        Notes:
          run terminal.exe.
        Args:
          conf(string): abs path of conf file. 
            details see mt4 help doc Client Terminal/Tools/Configuration at Startup 
        """
        import subprocess

        if conf:
            prog = '"%s"' % os.path.join(self.prog_path, self.mt_exe)
            conf = '/config:"%s"' % conf
            cmd = '%s %s' % (prog, conf)

            p = subprocess.Popen(cmd)
            p.wait()
            if p.returncode == 0:
                logging.info('cmd[%s] successded', cmd)
            else:
                err_msg = 'run mt4 with cmd[%s] failed!!' % cmd
                logging.error(err_msg)
                raise RuntimeError(err_msg)


def is_uac_enabled():
    """
    Note:
      check uac is enabled or not from reg value.
    Returns:
     True if uac is enabled, False if uac is disabled.
    """
    import winreg

    reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System',
                             0, winreg.KEY_READ)
    value, regtype = winreg.QueryValueEx(reg_key, 'EnableLUA')

    if value == 1:
        # reg value 1 means UAC is enabled
        return True
    else:
        return False


def get_appdata_path(program_file_dir):
    """
    Returns:
      AppData path corresponding to provided program file path
      e.g.: C:\\Users\\UserName\\AppData\\Roaming\\MetaQuotes\\Terminal\\7269C010EA668AEAE793BEE37C26ED57
    """
    app_data = os.environ.get('APPDATA')
    mt5_appdata_path = os.path.join(app_data, 'MetaQuotes', 'Terminal')

    app_dir = None

    walk_depth = 1
    for root, dirs, files in os.walk(mt5_appdata_path):
        # search ORIGIN_TXT until walk_depth
        depth = root[len(mt5_appdata_path):].count(os.path.sep)

        if ORIGIN_TXT in files:
            origin_file = os.path.join(root, ORIGIN_TXT)

            import codecs
            with codecs.open(origin_file, 'r', 'utf-16') as fp:
                line = fp.read()
                if line == program_file_dir:
                    app_dir = root
                    break

        if depth >= walk_depth:
            dirs[:] = []

    if app_dir is None:
        err_msg = '%s does not have appdata dir!.' % program_file_dir
        logging.error(err_msg)
        raise IOError(err_msg)

    return app_dir


def initizalize(ntpath, alias=DEFAULT_MT5_NAME):
    """
    Notes:
      initialize mt4
    Args:
      ntpath(string): mt4 install folder path.
        e.g.: C:\\Program Files (x86)\\MetaTrader 5 - Alpari Japan
      alias(string): mt4 object alias name. default value is DEFAULT_MT4_NAME
    """
    global _mt5s
    if alias not in _mt5s:
        # store mt4 objecct with alias name
        _mt5s[alias] = MT5(ntpath)
    else:
        logging.info('%s is already initialized' % alias)


def get_mt5(alias=DEFAULT_MT5_NAME):
    """
    Notes:
      return mt4 object which is initialized.
    Args:
      alias(string): mt4 object alias name. default value is DEFAULT_MT4_NAME
    Returns:
      mt4 object(metatrader.backtest.MT4): instantiated mt4 object
    """
    global _mt5s

    if alias in _mt5s:
        return _mt5s[alias]
    else:
        raise RuntimeError('mt5[%s] is not initialized.' % alias)
