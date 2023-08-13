__package_name__ = "BennieMocap"
__version__ = "v0.0.1"

from src.system.logging.configure import configure_logging

configure_logging()
import logging

logger = logging.getLogger(__name__)
logger.info(f"Initializing {__package_name__} package, version: {__version__}, from file: {__file__}")