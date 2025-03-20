import logging
import sys

from IPython.core.ultratb import AutoFormattedTB

# Configuração do logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('std.log', mode='w')
file_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
logger.addHandler(file_handler)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))

class MeuManipulador(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno == logging.ERROR:
            log_entry = self.format(record)
            if 'No such comm target registered' in str(record.msg):
                return
            logger.info(log_entry)

logger.addHandler(MeuManipulador())

# Instância que implementa o traceback
itb = AutoFormattedTB(mode='Plain', tb_offset=1)

def custom_exc(shell, etype, evalue, tb, tb_offset=None) -> None:
    # ainda imprime a mensagem de erro
    shell.showtraceback((etype, evalue, tb), tb_offset=tb_offset)
    # mas também registra no log como um erro
    logger.error('Uncaught exception', exc_info=(etype, evalue, tb))
