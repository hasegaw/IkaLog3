import logging


def init_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    handler_format = logging.Formatter('%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s')
    stream_handler.setFormatter(handler_format)

    logger.addHandler(stream_handler)


def get_logger():
    logger = logging.getLogger()
    return logger

if __name__ == '__main__':
    init_logger()
    logger =get_logger()
    logger.debug("hello")
