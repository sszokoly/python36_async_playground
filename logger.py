import logging

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)s]"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)

logger.debug("Test debug message")