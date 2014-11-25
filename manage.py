# -*- coding: utf-8 -*-

from logging import DEBUG, getLogger
from socket import setdefaulttimeout
from time import sleep
from traceback import print_exc

from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded
from flask.ext.script import Manager, Shell
from kombu import Exchange, Queue
from webassets.script import CommandLineEnvironment

from modules.database import get_mysql
from modules.models import (
    get_response,
    keyword,
    page,
    populate,
    proxy,
    result,
    start_task,
    statistics_memory,
    statistics_request,
    stop_task,
)

from serve import application, assets

from settings import BROKER, LOGGER_NAME, TIMEOUT

logger = getLogger(LOGGER_NAME)

setdefaulttimeout(TIMEOUT)

celery = Celery('manage')
celery.conf.update(
    BROKER=BROKER,
    BROKER_POOL_LIMIT=0,
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_ACKS_LATE=True,
    CELERY_IGNORE_RESULT=True,
    CELERY_QUEUES=(
        Queue(
            'celery_keyword',
            Exchange('default'),
            delivery_mode=1,
            routing_key='celery_keyword',
        ),
        Queue(
            'celery_page',
            Exchange('default'),
            delivery_mode=1,
            routing_key='celery_page',
        ),
        Queue(
            'celery_proxy_refresh',
            Exchange('default'),
            delivery_mode=1,
            routing_key='celery_proxy_refresh',
        ),
        Queue(
            'celery_proxy_verify',
            Exchange('default'),
            delivery_mode=1,
            routing_key='celery_proxy_verify',
        ),
    ),
    CELERY_RESULT_SERIALIZER='json',
    CELERY_ROUTES={
        'manage.celery_keyword': {
            'queue': 'celery_keyword',
        },
        'manage.celery_page': {
            'queue': 'celery_page',
        },
        'manage.celery_proxy_refresh': {
            'queue': 'celery_proxy_refresh',
        },
        'manage.celery_proxy_verify': {
            'queue': 'celery_proxy_verify',
        },
    },
    CELERY_TASK_SERIALIZER='json',
    CELERYD_MAX_TASKS_PER_CHILD=10,
    CELERYD_POOL_RESTARTS=True,
    CELERYD_PREFETCH_MULTIPLIER=1,
    CELERYD_TASK_SOFT_TIME_LIMIT=TIMEOUT * 2,
    CELERYD_TASK_TIME_LIMIT=TIMEOUT * 3,
)

manager = Manager(application, with_default_commands=False)


def make_context():
    return {
        'get_response': get_response,
        'mysql': get_mysql(),
        'keyword': keyword,
        'page': page,
        'proxy': proxy,
        'result': result,
        'statistics_memory': statistics_memory,
        'statistics_request': statistics_request,
    }

manager.add_command('shell', Shell(make_context=make_context))


@celery.task
def celery_keyword(id):
    mysql = get_mysql()
    instance = mysql.query(keyword).get(id)
    if instance.can_process():
        start_task('keyword', instance.id)
        try:
            instance.process()
        except SoftTimeLimitExceeded:
            print_exc()
        except Exception:
            print_exc()
        stop_task('keyword', instance.id)
    mysql.close()


@celery.task
def celery_page(id):
    mysql = get_mysql()
    instance = mysql.query(page).get(id)
    if instance.can_process():
        start_task('page', instance.id)
        try:
            instance.process()
        except SoftTimeLimitExceeded:
            print_exc()
        except Exception:
            print_exc()
        stop_task('page', instance.id)
    mysql.close()


@celery.task
def celery_proxy_refresh(id):
    try:
        mysql = get_mysql()
        instance = mysql.query(proxy).get(id)
        instance.refresh()
        mysql.close()
    except SoftTimeLimitExceeded:
        print_exc()
    except Exception:
        print_exc()


@celery.task
def celery_proxy_verify(id):
    try:
        mysql = get_mysql()
        instance = mysql.query(proxy).get(id)
        instance.verify()
        mysql.close()
    except SoftTimeLimitExceeded:
        print_exc()
    except Exception:
        print_exc()


@manager.command
def assets_():
    CommandLineEnvironment(assets, getLogger(LOGGER_NAME)).build()


@manager.command
def populate_():
    populate()


@manager.command
def statistics_memory_():
    value = 0
    stats = celery.control.inspect().stats()
    if not stats:
        return
    for key in stats:
        value = value + stats[key]['rusage']['maxrss']
    mysql = get_mysql()
    statistics_memory.insert(mysql, value)
    mysql.close()


@manager.command
def keywords():
    mysql = get_mysql()
    for instance in mysql.query(
        keyword,
    ).filter(
        keyword.status == 'New',
    ).order_by('id ASC').all():
        celery_keyword.delay(instance.id)
        logger.log(DEBUG, instance.string)
    mysql.close()
    sleep(60)


@manager.command
def pages():
    mysql = get_mysql()
    for instance in mysql.query(
        page,
    ).filter(
        page.status == 'New',
    ).order_by('id ASC').all():
        celery_page.delay(instance.id)
        logger.log(DEBUG, '%(string)s; %(start)s' % {
            'string': instance.keyword.string,
            'start': instance.start,
        })
    mysql.close()
    sleep(600)


@manager.command
def proxies_refresh():
    mysql = get_mysql()
    for instance in mysql.query(proxy).order_by('id ASC').all():
        if not instance.can_refresh():
            continue
        celery_proxy_refresh.delay(instance.id)
        logger.log(DEBUG, instance.url)
    mysql.close()
    sleep(60)


@manager.command
def proxies_verify():
    mysql = get_mysql()
    for instance in mysql.query(proxy).order_by('id ASC').all():
        if not instance.can_verify():
            continue
        celery_proxy_verify.delay(instance.id)
        logger.log(DEBUG, instance.url)
    mysql.close()

if __name__ == '__main__':
    manager.run()
