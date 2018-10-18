#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : config.py
# Author: jixin
# Date  : 18-10-17

import os
import uuid
import logging

basedir = os.path.abspath(os.path.dirname(__file__))


class InfoFilter(logging.Filter):
    def filter(self, record):
        """only use INFO
        筛选, 只需要 INFO 级别的log
        :param record:
        :return:
        """
        if logging.INFO <= record.levelno < logging.ERROR:
            # 已经是INFO级别了
            # 然后利用父类, 返回 1
            return super().filter(record)
        else:
            return 0


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or str(uuid.uuid4())
    SSL_DISABLE = False
    SQLALCHEMY_RECORD_QUERIES = True

    LOG_PATH = os.path.join(basedir, 'logs')
    LOG_PATH_ERROR = os.path.join(LOG_PATH, 'error.log')
    LOG_PATH_INFO = os.path.join(LOG_PATH, 'info.log')
    LOG_FILE_MAX_BYTES = 5 * 1024 * 1024
    LOG_FILE_BACKUP_COUNT = 5

    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'

    @staticmethod
    def init_app(app):
        pass


class DevConfig(Config):
    DEBUG = True
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:123456@127.0.0.1:3306/sqlprotest"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


class ProConfig(Config):
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:123456@127.0.0.1:3306/sqlpro"

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        import logging
        from logging.handlers import RotatingFileHandler
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(process)d %(thread)d '
            '%(pathname)s %(lineno)s %(message)s')

        file_handler_info = RotatingFileHandler(filename=cls.LOG_PATH_INFO)
        file_handler_info.setFormatter(formatter)
        file_handler_info.setLevel(logging.INFO)
        info_filter = InfoFilter()
        file_handler_info.addFilter(info_filter)
        app.logger.addHandler(file_handler_info)

        file_handler_error = RotatingFileHandler(filename=cls.LOG_PATH_ERROR)
        file_handler_error.setFormatter(formatter)
        file_handler_error.setLevel(logging.ERROR)
        app.logger.addHandler(file_handler_error)


config = {
    'development': DevConfig,
    'production': ProConfig,
    'default': DevConfig
}
