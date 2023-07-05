import logging
import datetime as dt


# GLOBAL VARIABLE
DEFAULT_PROPERTIES = logging.LogRecord('', '', '', '', '', '', '', '').__dict__.keys()


class LogEntityFormat(logging.Formatter):
    @staticmethod
    def ls0(num):
        if num < 10: return "0" + str(num)
        return str(num)

    def format(self, record):
        now      = dt.datetime.now()
        message  = record.getMessage()

        # DOCUMENT BASE MODEL
        document = {
            'date'      : self.ls0(now.year) + "-" + self.ls0(now.month ) + "-" + self.ls0(now.day),
            'time'      : self.ls0(now.hour) + ":" + self.ls0(now.minute) + ":" + self.ls0(now.second),
            'level'     : record.levelname,
            'message'   : message[1],
            'loggerName': record.name
        }

        # EXCEPTION MODEL
        if record.exc_info is not None:
            document.update({
                'exception': {
                    'message'   : str(record.exc_info[1]),
                    'code'      : 0,
                    'stackTrace': self.formatException(record.exc_info)
                }
            })

        # EXTRA CONTEXTUAL INFORMATION
        if len(DEFAULT_PROPERTIES) != len(record.__dict__):
            contextual_extra = set(record.__dict__).difference(set(DEFAULT_PROPERTIES))
            if contextual_extra:
                for key in contextual_extra:
                    document[key] = record.__dict__[key]
        return document
