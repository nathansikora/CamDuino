from time import asctime

LOG_FILE = 'log.txt'
IS_LOG_TO_FILE = True
LOG_STR = '{0}   :   {1}\n'


class Logger:
    @staticmethod
    def log(msg, path=LOG_FILE, is_log_to_file=IS_LOG_TO_FILE):
        msg = LOG_STR.format(asctime(), msg)
        print(msg)
        if is_log_to_file:
            with open(path, 'a') as ff:
                ff.write(msg)


