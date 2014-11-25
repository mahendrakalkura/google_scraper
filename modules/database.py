# -*- coding: utf-8 -*-

from redis import StrictRedis
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import ThreadLocalMetaData

from settings import MYSQL, REDIS

engine = create_engine(
    URL(**MYSQL),
    connect_args={
        'charset': 'utf8',
    },
    convert_unicode=True,
    encoding='utf-8',
    poolclass=NullPool,
)

base = declarative_base(bind=engine, metadata=ThreadLocalMetaData())


def get_mysql():
    return sessionmaker(autoflush=False, bind=engine)()


def get_redis():
    return StrictRedis(**REDIS)
