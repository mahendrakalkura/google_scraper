# -*- coding: utf-8 -*-

from logging import DEBUG, Formatter, StreamHandler, getLogger

from settings import LOGGER_NAME

formatter = Formatter('%(asctime)s [%(levelname)8s] %(message)s')

stream_handler = StreamHandler()
stream_handler.setLevel(DEBUG)
stream_handler.setFormatter(formatter)

logger = getLogger(LOGGER_NAME)
logger.setLevel(DEBUG)
logger.addHandler(stream_handler)


def initialize():
    pass
