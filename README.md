Installation
============

**Step 1:**

```
$ mkdir google_scraper
```

**Step 2:**

```
$ cd google_scraper
$ git clone git@bitbucket.org:nemeigh/google_scraper.git .
$ cp --archive settings.py.sample settings.py # edit as required
```

**Step 3:**

```
$ cd google_scraper
$ mysql -e 'CREATE DATABASE google_scraper'
$ mysql google_scraper < files/0.sql
$ mysql google_scraper < files/1.sql
```

**Step 4:**

```
$ cd google_scraper
$ mkvirtualenv google_scraper
$ pip install -r requirements.txt
```

**Step 5:**

```
$ cd google_scraper
$ bower install
```

**Step 6:**

```
$ cd google_scraper
$ workon google_scraper
$ python manage.py assets_
```

Execution
=========

**crontab:**

```
* * * * * cd $HOME/google_scraper && $HOME/.virtualenvs/google_scraper/bin/python manage.py statistics_memory_
```

**supervisor:**

```
[program:google_scraper_manage_py_celery_keyword]
autorestart=true
autostart=true
command=$HOME/.virtualenvs/google_scraper/bin/celery worker --app=manage --concurrency=10 --hostname=celery_keyword --loglevel=WARNING --pool=prefork --queues=celery_keyword
directory=$HOME/google_scraper
startsecs=0
```

```
[program:google_scraper_manage_py_celery_page]
autorestart=true
autostart=true
command=$HOME/.virtualenvs/google_scraper/bin/celery worker --app=manage --concurrency=100 --hostname=celery_page --loglevel=WARNING --pool=prefork --queues=celery_page
directory=$HOME/google_scraper
startsecs=0
```

```
[program:google_scraper_manage_py_celery_proxy_refresh]
autorestart=true
autostart=true
command=$HOME/.virtualenvs/google_scraper/bin/celery worker --app=manage --concurrency=10 --hostname=celery_proxy_refresh --loglevel=WARNING --pool=prefork --queues=celery_proxy_refresh
directory=$HOME/google_scraper
startsecs=0
```

```
[program:google_scraper_manage_py_keywords]
autorestart=true
autostart=true
command=$HOME/.virtualenvs/google_scraper/bin/python manage.py keywords
directory=$HOME/google_scraper
startsecs=0
```

```
[program:google_scraper_manage_py_pages]
autorestart=true
autostart=true
command=$HOME/.virtualenvs/google_scraper/bin/python manage.py pages
directory=$HOME/google_scraper
startsecs=0
```

```
[program:google_scraper_manage_py_proxies_refresh]
autorestart=true
autostart=true
command=$HOME/.virtualenvs/google_scraper/bin/python manage.py proxies_refresh
directory=$HOME/google_scraper
startsecs=0
```

```
[program:google_scraper_serve_py]
autorestart=true
autostart=true
command=$HOME/.virtualenvs/google_scraper/bin/python serve.py
directory=$HOME/google_scraper
startsecs=0
```
