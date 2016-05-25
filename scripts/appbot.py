import argparse
import json
import os
import requests
import urlparse
import utils
from urllib import urlencode


CONFIGS_PATH = 'configs'

DEFAULT_HEADER = 'application/json; charset=utf8'
ISO_FMT = '%Y-%m-%dT%H:%M:%S'
APP_ID_TAG = '%%APPID%%'
BASE_URL = 'https://api.appbot.co/api/v1/apps/%s' % APP_ID_TAG


global CONFIG
CONFIG = None
"""
    CONFIG = {
        'account_key': '<value>',
        'ios': '<ios_id>',
        'android': '<android_id>',
    }
"""


def _mount_app_id(url, app):
    app_id = CONFIG.get(app)
    return url.replace(APP_ID_TAG, app_id)


def _execute_with_pagination(url, params, method, page=1):
    while True:
        params.update({'page': page})
        result_url = utils._mount_parameters(url, params)
        success, result = utils.get(result_url)
        if not success:
            raise Exception('Failed fetching reviews. Reason: [%s]' % result)
        for r in result['results']:
            yield r
        page += 1
        if page > result['total_pages']:
            break


def load_appbot_config(keys_config_file=os.path.join(CONFIGS_PATH, 'appbot_config.json')):
    global CONFIG
    if not CONFIG:
        with open(keys_config_file, 'rb') as fh:
            CONFIG = json.load(fh)
    return CONFIG


def fetch_reviews(start_date, end_date, app, fields=[]):
    load_appbot_config()
    app_base_url = _mount_app_id(BASE_URL, app)
    url = utils._mount.url([app_base_url, 'reviews'])
    url = _mount_app_id(url, app)
    params = {'start': start_date, 'end': end_date}
    for i in _execute_with_pagination(url, params, method=utils.get, page=1):
        if fields:
            i = dict([(k, v) for k, v in r.items() if k in fields])
        i['app'] = app
        yield i


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument()
    args = parser.parse_args()


