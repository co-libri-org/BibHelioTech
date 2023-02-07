import os
from pprint import pprint

from bht_config import yml_settings


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or \
                 b'\x82\xde\x96\xc5L\xb4c\xd5\x17\x12*\x12\xd3\xd4\xb7\xf5'
    ALLOWED_EXTENSIONS = ['pdf']

    def __init__(self):
        # pprint(yml_settings)
        self.__dict__.update(yml_settings)
        self.__dict__['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
                                                   os.path.join(yml_settings['WEB_DB_DIR'], 'bht_web.db')
