
import os
from pymongo import MongoClient
import redis

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'ngle_api_tongchun')
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True

    MONGO_HOST = 'mongodb://admin:1234@54.180.122.32/usa_db'

    MONGO_CLI = MongoClient(MONGO_HOST)
    REDIS_CLI = redis.Redis(host='54.180.122.32', port=6379, db=0)


class ProductionConfig(Config):
    DEBUG = False

    MONGO_HOST = 'mongodb://admin:1234@127.0.0.1/usa_db'

    MONGO_CLI = MongoClient(MONGO_HOST)
    REDIS_CLI = redis.Redis(host='127.0.0.1', port=6379, db=0)


config_via_env = dict(
    dev=DevelopmentConfig,
    prod=ProductionConfig
)

