# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from logging import DEBUG, getLogger
from re import compile
from string import lowercase
from time import time
from traceback import print_exc
from uuid import uuid4
from urlparse import parse_qs, urlparse

from human_curl import get
from scrapy.selector import Selector
from sqlalchemy import Column, Integer
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.session import Session
from urllib import quote_plus

from modules.database import base, get_mysql, get_redis

from settings import LOGGER_NAME, TIMEOUT

logger = getLogger(LOGGER_NAME)

num = 100

pattern = compile('^[0-9]')


class proxy(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'proxies'

    id = Column(Integer(), primary_key=True)

    proxy = relationship(
        'proxy',
        backref=backref('proxies', cascade='all', lazy='dynamic'),
        remote_side=id,
    )

    @classmethod
    def insert(
        proxy,
        mysql,
        proxy_,
        url,
        protocol,
        type,
        durations_refresh,
        durations_ban,
        durations_reuse,
    ):
        mysql.add(proxy(**{
            'durations_ban': durations_ban,
            'durations_refresh': durations_refresh,
            'durations_reuse': durations_reuse,
            'protocol': protocol,
            'proxy': proxy_,
            'timestamps_ban': None,
            'timestamps_refresh': None,
            'timestamps_reuse': None,
            'type': type,
            'url': url,
        }))
        try:
            mysql.commit()
        except Exception:
            print_exc()
            mysql.rollback()

    @classmethod
    def select(proxy, mysql):
        try:
            return mysql.query(
                proxy,
            ).get(
                mysql.connection().execute(
                    '''
                    SELECT id
                    FROM proxies
                    WHERE
                        url NOT LIKE 'http%%'
                        AND
                        (
                            timestamps_ban IS NULL
                            OR
                            DATE_ADD(
                                timestamps_ban, INTERVAL durations_ban SECOND
                            )
                            <
                            NOW()
                        )
                        AND
                        (
                            timestamps_reuse IS NULL
                            OR
                            DATE_ADD(
                                timestamps_reuse,
                                INTERVAL durations_reuse SECOND
                            )
                            <
                            NOW()
                        )
                    ORDER BY timestamps_ban ASC , timestamps_reuse ASC
                    LIMIT 1
                    OFFSET 0
                    '''
                ).fetchone()[0]
            )
        except TypeError:
            pass

    def refresh(self):
        if not self.can_refresh():
            return
        mysql = Session.object_session(self)
        response = get_response(self.url, None)
        if not response:
            logger.log(DEBUG, '%(url)s; Failure (#1)' % {
                'url': self.url,
            })
            return
        if not response.status_code == 200:
            logger.log(DEBUG, '%(url)s; Failure (#2)' % {
                'url': self.url,
            })
            return
        urls = sorted(set([
            url.strip() for url in response.content.split('\n') if url.strip()
        ]))
        if not urls:
            logger.log(DEBUG, '%(url)s; Failure (#3)' % {
                'url': self.url,
            })
            return
        logger.log(DEBUG, '%(url)s; Success; %(len_urls)s' % {
            'url': self.url,
            'len_urls': len(urls),
        })
        for url in urls:
            if not pattern.search(url):
                logger.log(DEBUG, '%(url)s; %(url_)s; Failure (#1)' % {
                    'url': self.url,
                    'url_': url,
                })
                continue
            if mysql.query(proxy).filter(proxy.url==url).count():
                logger.log(DEBUG, '%(url)s; %(url_)s; Failure (#2)' % {
                    'url': self.url,
                    'url_': url,
                })
                continue
            proxy.insert(
                mysql,
                self,
                url,
                self.protocol,
                self.type,
                self.durations_refresh,
                self.durations_ban,
                self.durations_reuse,
            )
            logger.log(DEBUG, '%(url)s; %(url_)s; Success' % {
                'url': self.url,
                'url_': url,
            })
        mysql.query(
            proxy,
        ).filter(
            proxy.proxy==self, ~proxy.url.in_(urls),
        ).delete(
            synchronize_session=False,
        )
        try:
            mysql.commit()
        except Exception:
            print_exc()
            mysql.rollback()
        self.timestamps_refresh = datetime.now()
        mysql.add(self)
        try:
            mysql.commit()
        except Exception:
            print_exc()
            mysql.rollback()

    def verify(self):
        if not self.can_verify():
            return
        response = get_response(
            'https://google.com/search?num=%(num)s&q=%(q)s' % {
                'num': num,
                'q': quote_plus(uuid4().hex),
            },
            self
        )
        if not response:
            logger.log(DEBUG, '%(url)s; Failure (#1)' % {
                'url': self.url,
            })
            return
        if not response.status_code == 200:
            logger.log(DEBUG, '%(url)s; Failure (#2)' % {
                'url': self.url,
            })
            return
        if has_captcha(response.content):
            logger.log(DEBUG, '%(url)s; Failure (#3)' % {
                'url': self.url,
            })
            return
        logger.log(DEBUG, '%(url)s; Success' % {
            'url': self.url,
        })

    def get_tuple(self):
        hostname, port = self.url.split(':', 2)
        return (str(self.protocol.lower()), (str(hostname), int(port)))

    def set_ban(self):
        mysql = Session.object_session(self)
        self.timestamps_ban = datetime.now()
        mysql.add(self)
        try:
            mysql.commit()
        except Exception:
            print_exc()
            mysql.rollback()

    def set_reuse(self):
        mysql = Session.object_session(self)
        self.timestamps_reuse = datetime.now()
        mysql.add(self)
        try:
            mysql.commit()
        except Exception:
            print_exc()
            mysql.rollback()

    def can_refresh(self):
        if not self.url.startswith('http'):
            return False
        if (
            self.timestamps_refresh
            and
            self.timestamps_refresh + timedelta(seconds=self.durations_refresh)
            >=
            datetime.now()
        ):
            return False
        return True

    def can_verify(self):
        if self.url.startswith('http'):
            return False
        now = datetime.now()
        if (
            self.timestamps_ban
            and
            self.timestamps_ban + timedelta(seconds=self.durations_ban) >= now
        ):
            return False
        if (
            self.timestamps_reuse
            and
            self.timestamps_reuse + timedelta(seconds=self.durations_reuse)
            >=
            now
        ):
            return False
        return True


class keyword(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'keywords'

    def process(self):
        mysql = Session.object_session(self)
        now = datetime.now()
        start = 0
        status = 'New'
        mysql.add(page(**{
            'keyword': self,
            'start': start,
            'status': status,
            'timestamps_insert': now,
            'timestamps_update': now,
        }))
        try:
            mysql.commit()
        except Exception:
            print_exc()
            mysql.rollback()
        logger.log(DEBUG, '%(string)s; %(start)s; %(status)s' % {
            'start': start,
            'status': status,
            'string': self.string,
        })
        self.status = 'Pending'
        self.timestamps_update = now
        mysql.add(self)
        try:
            mysql.commit()
        except Exception:
            print_exc()
            mysql.rollback()
        logger.log(DEBUG, '%(string)s; %(status)s' % {
            'status': self.status,
            'string': self.string,
        })

    def can_process(self):
        if not self.status == 'New':
            return False
        if has_task('keyword', self.id):
            return False
        return True

keyword.__table__.choices = {
    'status': [
        'New',
        'Pending',
        'Completed',
    ],
}


class page(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'pages'

    keyword = relationship(
        'keyword', backref=backref('pages', cascade='all', lazy='dynamic'),
    )

    def process(self):
        mysql = Session.object_session(self)
        start = 0
        results = []
        try:
            start, results = get_start_and_results(
                mysql, self.keyword.string, self.start
            )
        except (TypeError, ValueError):
            pass
        if not start and not results:
            logger.log(DEBUG, '%(string)s; %(start)s; %(status)s' % {
                'start': self.start,
                'status': self.status,
                'string': self.keyword.string,
            })
            return
        logger.log(DEBUG, '%(string)s; %(start)s; %(results)s' % {
            'results': len(results),
            'start': self.start,
            'string': self.keyword.string,
        })
        now = datetime.now()
        for r in results:
            if not mysql.query(
                result,
            ).filter(
                result.page == self, result.rank == r['rank'],
            ).count():
                mysql.add(result(**{
                    'page': self,
                    'rank': r['rank'],
                    'url': r['url'],
                }))
                try:
                    mysql.commit()
                except Exception:
                    print_exc()
                    mysql.rollback()
                logger.log(
                    DEBUG,
                    '%(string)s; %(start)s; %(rank)s; %(url)s' % {
                        'rank': r['rank'],
                        'start': self.start,
                        'string': self.keyword.string,
                        'url': r['url'],
                    }
                )
        self.status = 'Completed'
        self.timestamps_update = now
        mysql.add(self)
        try:
            mysql.commit()
        except Exception:
            print_exc()
            mysql.rollback()
        logger.log(DEBUG, '%(string)s; %(start)s; %(status)s' % {
            'start': self.start,
            'status': self.status,
            'string': self.keyword.string,
        })
        if start > 900:
            self.keyword.status = 'Completed'
            self.keyword.timestamps_update = now
            mysql.add(self.keyword)
            try:
                mysql.commit()
            except Exception:
                print_exc()
                mysql.rollback()
        else:
            if not mysql.query(
                page,
            ).filter(
                page.keyword == self.keyword, page.start == start,
            ).count():
                status = 'New'
                mysql.add(page(**{
                    'keyword': self.keyword,
                    'start': start,
                    'status': status,
                    'timestamps_insert': datetime.now(),
                    'timestamps_update': datetime.now(),
                }))
                try:
                    mysql.commit()
                except Exception:
                    print_exc()
                    mysql.rollback()
                logger.log(DEBUG, '%(string)s; %(start)s; %(status)s' % {
                    'start': start,
                    'status': status,
                    'string': self.keyword.string,
                })
        logger.log(DEBUG, '%(string)s; %(status)s' % {
            'string': self.keyword.string,
            'status': self.keyword.status,
        })

    def can_process(self):
        if not self.status == 'New':
            return False
        if has_task('page', self.id):
            return False
        return True

page.__table__.choices = {
    'status': [
        'New',
        'Completed',
    ],
}


class result(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'results'

    page = relationship(
        'page', backref=backref('results', cascade='all', lazy='dynamic'),
    )


class statistics_memory(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'statistics_memories'

    @classmethod
    def insert(statistics_memory, mysql, value):
        mysql.add(statistics_memory(**{
            'timestamp': datetime.now(),
            'value': value,
        }))
        try:
            mysql.commit()
        except Exception:
            print_exc()
            mysql.rollback()


class statistics_request(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'statistics_requests'

    proxy = relationship(
        'proxy',
        backref=backref('statistics_requests', cascade='all', lazy='dynamic'),
    )

    @classmethod
    def insert(
        statistics_request,
        mysql,
        proxy,
        url,
        content_length,
        status_code,
        has_captcha,
        duration,
    ):
        mysql.add(statistics_request(**{
            'content_length': content_length,
            'duration': duration,
            'has_captcha': has_captcha,
            'proxy': proxy,
            'status_code': status_code,
            'timestamp': datetime.now(),
            'url': url,
        }))
        try:
            mysql.commit()
        except Exception:
            print_exc()
            mysql.rollback()


def populate():
    mysql = get_mysql()
    for instance in mysql.query(keyword).order_by('id ASC').all():
        mysql.delete(instance)
        try:
            mysql.commit()
        except Exception:
            print_exc()
            mysql.rollback()
    for string in lowercase:
        mysql.add(keyword(**{
            'status': 'New',
            'string': string,
            'timestamps_insert': datetime.now(),
            'timestamps_update': datetime.now(),
        }))
        try:
            mysql.commit()
        except Exception:
            print_exc()
            mysql.rollback()
    mysql.close()


def start_task(class_, id):
    get_redis().setex(get_key(class_, id), TIMEOUT, 1)


def stop_task(class_, id):
    get_redis().delete(get_key(class_, id))


def get_response(url, proxy):
    try:
        return get(
            str(url),
            allow_redirects=True,
            connection_timeout=TIMEOUT,
            proxy=proxy.get_tuple() if proxy else None,
            timeout=TIMEOUT,
            validate_cert=False,
        )
    except Exception:
        print_exc()


def get_contents(mysql, url):
    with get_redis().lock('get_contents', timeout=TIMEOUT * 3):
        p = proxy.select(mysql)
        if not p:
            return
        p.set_reuse()
    one = time()
    response = get_response(url, p)
    two = time()
    with get_redis().lock('get_contents', timeout=TIMEOUT * 3):
        if (
            response
            and
            response.status_code == 200
            and
            not has_captcha(response.content)
        ):
            p.set_reuse()
        else:
            p.set_ban()
    statistics_request.insert(
        mysql,
        p,
        url,
        len(response.content) if response and response.content else 0,
        response.status_code if response and response.status_code else 999,
        'Yes'
        if response and response.content and has_captcha(response.content)
        else 'No',
        round(two - one, 6),
    )
    logger.log(
        DEBUG,
        '%(url)s; %(content_length)s; %(status_code)s; %(has_captcha)s; '
        '%(duration)9.6f' % {
            'content_length':
            len(response.content) if response and response.content else 0,
            'duration': two - one,
            'has_captcha':
            'Yes'
            if response and response.content and has_captcha(response.content)
            else 'No',
            'status_code':
            response.status_code if response and response.status_code else 999,
            'url': url,
        }
    )
    return response.content if response and response.content else None


def get_start_and_results(mysql, q, start):
    contents = get_contents(
        mysql,
        'https://google.com/search?num=%(num)s&q=%(q)s&start=%(start)s' % {
            'num': num,
            'q': quote_plus(q),
            'start': start,
        }
    )
    if not contents:
        return
    start_ = 0
    results = []
    selector = Selector(text=contents)
    if 'Next' in selector.xpath('//td[@class="b"]/a/span/text()').extract():
        start_ = start + num
    index = 0
    for li in selector.xpath('//li[@class="g"]'):
        href = get_href(li)
        if not href:
            continue
        href = urlparse('http://google.com%(href)s' % {
            'href': href,
        })
        if 'google.com' in href.netloc:
            href = parse_qs(href.query)['q'][0].strip('/')
            if not href.startswith('http'):
                continue
            index += 1
            results.append({
                'rank': start + index,
                'url': href,
            })
    return start_, results


def get_href(li):
    if li.xpath('.//h3[@class="r"]').extract():
        return li.xpath('.//h3[@class="r"]/a/@href').extract()[0]
    if li.xpath(
        './/table[@class="ts"]/tbody/tr/td/h3[@class="r"]'
    ).extract():
        return li.xpath(
            './/table[@class="ts"]/tbody/tr/td/h3[@class="r"]/a/@href'
        ).extract()[0]


def get_key(class_, id):
    return '%(class)s-%(id)s' % {
        'class': class_,
        'id': id,
    }


def has_captcha(contents):
    if Selector(
        text=contents,
    ).xpath('//form[@action="CaptchaRedirect"]').extract():
        return True
    return False


def has_task(class_, id):
    if not get_redis().get(get_key(class_, id)):
        return False
    return True
