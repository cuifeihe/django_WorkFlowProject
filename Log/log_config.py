import logging

class LogConfig(object):
    """
    错误日志记录的相关配置
    """

    def __init__(self, logger_name, path, content,
                 format_str="----------------------------------------------------------------------------------------\n"
                            "时间:%(asctime)s - 级别:%(levelname)s - 文件:%(filename)s - 函数:%(name)s - 源码行号:%(lineno)d \n"
                            "日志信息:%(message)s \n"
                            "----------------------------------------------------------------------------------------",
                 level='WARNING', encoding='utf-8', mode='a+'):
        self.logger_name = logger_name
        self.path = path
        self.content = content
        self.level = level
        self.mode = mode
        self.encoding = encoding
        # self.cur_path = os.path.abspath('..')
        self.format = format_str
        self.logger = None
        self.handler = None
        self.formatter = None
        self.init_logger()

    def create_logger(self):
        self.logger = logging.Logger(self.logger_name)

    def create_handler(self):
        self.handler = logging.FileHandler(self.path, encoding=self.encoding, mode=self.mode)

    def set_level(self):
        self.handler.setLevel(self.level)

    def create_formatter(self):
        self.formatter = logging.Formatter(self.format)

    def bind_handler_logger(self):
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)

    def init_logger(self):
        self.create_logger()
        self.create_handler()
        self.create_formatter()
        self.set_level()
        self.bind_handler_logger()
        self.logger.warning(self.content)

