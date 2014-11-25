# -*- coding: utf-8 -*-

from collections import Counter
from datetime import datetime, timedelta
from os.path import abspath, dirname, join

from flask import Flask, jsonify, render_template
from flask.ext.assets import Bundle, Environment
from numpy import mean, median
from sqlalchemy import func

from modules.database import get_mysql
from modules.models import (
    page, proxy, result, statistics_memory, statistics_request,
)
from modules.log import initialize

initialize()

application = Flask(
    __name__, static_folder=join(abspath(dirname(__file__)), 'resources'),
)

application.config.from_pyfile('settings.py')

assets = Environment(application)
assets.cache = not application.config['DEBUG']
assets.debug = application.config['DEBUG']
assets.directory = application.static_folder
assets.manifest = 'json:assets/versions.json'
assets.url = application.static_url_path
assets.url_expire = True
assets.versions = 'hash'
assets.register('javascripts', Bundle(
    'vendor/jquery/dist/jquery.js',
    'vendor/angular/angular.min.js',
    'vendor/bootstrap/dist/js/bootstrap.js',
    'vendor/highcharts/highcharts-all.js',
    'javascripts/all.js',
    filters='rjsmin' if not application.config['DEBUG'] else None,
    output='assets/compressed.js',
))
assets.register('stylesheets', Bundle(
    Bundle(
        'stylesheets/all.less', filters='less', output='stylesheets/all.css',
    ),
    filters='cssmin,cssrewrite' if not application.config['DEBUG'] else None,
    output='assets/compressed.css',
))


@application.route('/')
def index():
    return render_template('index.html')


@application.route('/memories', methods=['POST'])
def memories():
    series = [{
        'data': [],
        'name': 'Timestamp',
    }]
    x_axis_categories = []
    mysql = get_mysql()
    for instance in mysql.query(
        statistics_memory.value,
        statistics_memory.timestamp,
    ).order_by('timestamp DESC')[0:30]:
        series[0]['data'].append(round((instance.value * 1.00 / 1024), 2))
        x_axis_categories.append(instance.timestamp.isoformat(' ')[10:])
    mysql.close()
    series[0]['data'] = series[0]['data'][::-1]
    return jsonify({
        'series': series,
        'x_axis_categories': x_axis_categories[::-1],
    })


@application.route('/proxies', methods=['POST'])
def proxies():
    mysql = get_mysql()

    proxies = 0
    proxies_non_sources = 0
    proxies_non_sources_banned = 0
    proxies_non_sources_used = 0
    proxies_non_sources_unused = 0
    proxies = mysql.query(proxy.id).count()
    last_updated_on = 'N/A'

    now = datetime.now()

    proxies_sources = mysql.query(
        proxy.id,
    ).filter(
        proxy.url.like('http%'),
    ).count()
    for instance in mysql.query(
        proxy.durations_ban,
        proxy.durations_reuse,
        proxy.timestamps_ban,
        proxy.timestamps_reuse,
    ).filter(
        ~proxy.url.like('http%'),
    ).all():
        proxies_non_sources += 1
        if instance.timestamps_ban:
            if (
                instance.timestamps_ban
                +
                timedelta(seconds=instance.durations_ban)
                >=
                now
            ):
                proxies_non_sources_banned += 1
                continue
        if instance.timestamps_reuse:
            if (
                instance.timestamps_reuse
                +
                timedelta(seconds=instance.durations_reuse)
                >=
                now
            ):
                proxies_non_sources_used += 1
                continue
        proxies_non_sources_unused += 1

    try:
        last_updated_on = mysql.query(
            func.max(proxy.timestamps_refresh),
        ).first()[0].isoformat(' ')
    except AttributeError:
        pass

    mysql.close()

    return jsonify({
        'last_updated_on': last_updated_on,
        'proxies': proxies,
        'proxies_non_sources': proxies_non_sources,
        'proxies_non_sources_banned': proxies_non_sources_banned,
        'proxies_non_sources_unused': proxies_non_sources_unused,
        'proxies_non_sources_used': proxies_non_sources_used,
        'proxies_sources': proxies_sources,
    })


@application.route('/statistics_requests', methods=['POST'])
def statistics_requests():
    mysql = get_mysql()

    status_codes = mysql.query(
        statistics_request.status_code,
        func.count(statistics_request.status_code),
    ).group_by(
        statistics_request.status_code,
    ).order_by(
        func.count(statistics_request.status_code).desc(),
    ).all()

    has_captchas = mysql.query(
        statistics_request.has_captcha,
        func.count(statistics_request.has_captcha),
    ).group_by(
        statistics_request.has_captcha,
    ).order_by(
        func.count(statistics_request.has_captcha).desc(),
    ).all()

    requests = 0
    requests_per_day = 0
    requests_per_hour = 0
    requests_per_minute = 0
    requests_per_second = 0
    last_updated_on = 'N/A'

    requests = mysql.query(statistics_request.id).count()
    if requests:
        first = mysql.query(func.min(statistics_request.timestamp)).first()[0]
        last = mysql.query(func.max(statistics_request.timestamp)).first()[0]
        if first and last:
            seconds = (last - first).total_seconds()
            requests_per_second = (requests * 1.00) / seconds
            requests_per_minute = requests_per_second * 60.00
            requests_per_hour = requests_per_second * 60.00 * 60.00
            requests_per_day = requests_per_second * 60.00 * 60.00 * 24.00
            last_updated_on = last.isoformat(' ')

    durations_minimum = 0
    durations_maximum = 0
    durations_mean = 0
    durations_median = 0
    durations_mode = 0
    last_updated_on = 'N/A'

    durations = [
        float(instance.duration)
        for instance in mysql.query(statistics_request.duration).all()
        if instance.duration
    ]
    if durations:
        durations_minimum = min(durations)
        durations_maximum = max(durations)
        durations_mean = mean(durations)
        durations_median = median(durations)
        durations_mode = Counter(durations).most_common(1)[0][0]

    try:
        last_updated_on = mysql.query(
            func.max(statistics_request.timestamp),
        ).first()[0].isoformat(' ')
    except AttributeError:
        pass

    mysql.close()

    return jsonify({
        'durations_maximum': durations_maximum,
        'durations_mean': durations_mean,
        'durations_median': durations_median,
        'durations_minimum': durations_minimum,
        'durations_mode': durations_mode,
        'has_captchas': has_captchas,
        'last_updated_on': last_updated_on,
        'requests': requests,
        'requests_per_day': requests_per_day,
        'requests_per_hour': requests_per_hour,
        'requests_per_minute': requests_per_minute,
        'requests_per_second': requests_per_second,
        'status_codes': status_codes,
    })


@application.route('/results', methods=['POST'])
def results():
    mysql = get_mysql()

    results = 0
    results_per_day = 0
    results_per_hour = 0
    results_per_minute = 0
    results_per_second = 0
    last_updated_on = 'N/A'

    results = mysql.query(result.id).count()
    if results:
        first = mysql.query(func.min(page.timestamps_insert)).first()[0]
        last = mysql.query(func.max(page.timestamps_update)).first()[0]
        if first and last:
            seconds = (last - first).total_seconds()
            results_per_second = (results * 1.00) / seconds
            results_per_minute = results_per_second * 60.00
            results_per_hour = results_per_second * 60.00 * 60.00
            results_per_day = results_per_second * 60.00 * 60.00 * 24.00
            last_updated_on = last.isoformat(' ')

    mysql.close()

    return jsonify({
        'last_updated_on': last_updated_on,
        'results': results,
        'results_per_day': results_per_day,
        'results_per_hour': results_per_hour,
        'results_per_minute': results_per_minute,
        'results_per_second': results_per_second,
    })

if __name__ == '__main__':
    application.run(
        host=application.config['HOST'],
        port=application.config['PORT'],
        processes=application.config['PROCESSES'],
    )
