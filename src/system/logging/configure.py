import logging
import logging.handlers
import sys
from logging.config import dictConfig

DEFAULT_LOGGING = {"version": 1, "disable_existing_loggers": False}

LOG_FILE_PATH = None

format_string = "[%(asctime)s.%(msecs)04d] [%(levelname)8s] [%(name)s] [%(funcName)s():%(lineno)s] [PID:%(process)d TID:%(thread)d] %(message)s"

default_formatter = logging.Formatter(fmt=format_string, datefmt="%Y-%m-%d %H:%M:%S")

log_view_format_string = "[%(asctime)s.%(msecs)04d] [%(levelname)4s] [%(name)s] [Process:%(process)d Thread:%(thread)d] ::::: [%(name)s:%(funcName)s():%(lineno)s] |||| %(message)s."

def _get_handlers():
    dictConfig(DEFAULT_LOGGING)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(default_formatter)

    return [console_handler]

def configure_logging():
    print(f"Setting up logging {__file__}")

    if len(logging.getLogger().handlers) == 0:
        handlers = _get_handlers()
        for handler in handlers:
            if handler not in logging.getLogger("").handlers:
                logging.getLogger("").handlers.append(handler)
        logging.root.setLevel(logging.DEBUG)
    else:
        logger = logging.getLogger(__name__)
        logger.info("Logging already configured")