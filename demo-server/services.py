import os
import logging.config
import traceback


class LogService:
    LOG_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)))
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'norm': {
                'format': '%(asctime)s %(threadName)s %(levelname)s %(filename)s:%(lineno)d - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'norm'
            }
        },
        'loggers': {}
    }

    __loggers = {
    }

    @classmethod
    def __create_logger(cls, name):
        if name in cls.LOGGING_CONFIG['loggers']:
            return logging.getLogger(name)

        cls.LOGGING_CONFIG['handlers'][name] = {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(cls.LOG_ROOT, name + '.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 3,
            'formatter': 'norm',
            'encoding': 'utf8'
        }
        cls.LOGGING_CONFIG['loggers'][name] = {
            'handlers': ['console', name],
            'level': 'INFO'
        }

        logging.config.dictConfig(cls.LOGGING_CONFIG)
        return logging.getLogger(name)

    @classmethod
    def get_logger(cls, name=None):
        if name is None:
            name = 'root'
        logger = cls.__loggers.get(name)
        if logger is None:
            logger = cls.__create_logger(name)
            cls.__loggers[name] = logger
        return logger

    @classmethod
    def error(cls, msg, *args, **kwargs):
        if isinstance(msg, Exception):
            cls.get_logger().error(traceback.format_exc(), *args, **kwargs)
        else:
            cls.get_logger().error(msg, *args, **kwargs)

    @classmethod
    def info(cls, msg, *args, **kwargs):
        cls.get_logger().info(msg, *args, **kwargs)

    @classmethod
    def debug(cls, msg, *args, **kwargs):
        cls.get_logger().debug(msg, *args, **kwargs)
