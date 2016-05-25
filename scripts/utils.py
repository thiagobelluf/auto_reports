import atexit
import csv
import json
import os
import requests
import sys
import tempfile
from datetime import timedelta
from dateutil import parser


global SESSION
SESSION = None

ISO_FMT = '%Y-%m-%dT%H:%M:%S'


def log(msg):
    print >> sys.stderr, msg


def _load_session():
    global SESSION
    if not SESSION:
        SESSION = requests.session()
    return SESSION


def _mount_url(url_parts):
    return '/'.join([url.strip('/') for url in url_parts])


def _mount_parameters(url, params):
    _POS = 4
    params.update({'key': CONFIG.get('account_key')})
    parsed_url = list(urlparse.urlsplit(url))
    query = dict(urlparse.parse_qsl(parsed_url[_POS]))
    query.update(params)
    parsed_url[_POS] = urlencode(query)
    parsed_url.append('')
    url_result = urlparse.urlunparse(parsed_url)
    return url_result


def get(url):
    _load_session()
    res = SESSION.get(url, headers={'content-type': DEFAULT_HEADER})
    if res.status_code == 200:
        return True, res.json()
    else:
        return False, res.reason


def post(url, data):
    _load_session()
    res = SESSION.post(url, headers={'content-type': DEFAULT_HEADER}, data=data)
    if res.status_code == 200:
        return True, None
    else:
        return False, res.reason


def iterate_date(start_datetime, end_datetime):
    st = parser.parse(start_datetime)
    et = parser.parse(end_datetime)

    interval = et - st
    if interval.days < 0:
        raise Exception('End time (%s) < Start time (%s)' % (end_datetime, start_datetime))

    days = interval.days
    for i in range(1, days + 1):
        yield st.strftime(ISO_FMT), (st + timedelta(days=1)).strftime(ISO_FMT)
        st += timedelta(days=1)


def load_from_csv_file(f_path):
    log('[CSV File] Loading content from csv: [%s]' % f_path)
    if f_path:
        with open(f_path, 'rb') as fh:
            reader = csv.DictReader(fh)
            for i in reader:
                yield i


def dump_to_csv_file(content, fieldnames=None, output_fpath=None):
    def utf_8_encoder(data):
        for k in data.keys():
            if isinstance(data[k], basestring):
                data[k] = data[k].encode('utf-8')
        return data


    output_fpath = output_fpath or make_tmp_file()
    log('[CSV File] Dumping content to csv: [%s]' % output_fpath)
    output = open(output_fpath,  'wb')
    writer = None
    for c in content:
        if not writer:
            writer = csv.DictWriter(output, fieldnames=fieldnames or c.keys())
            writer.writeheader()
        writer.writerow(utf_8_encoder(c))
    output.close()
    return output_fpath


def make_tmp_file():
    _, fpath = tempfile.mkstemp()
    def _remove_file(fpath):
        log('[AtExit] Removing file: [%s]' % fpath)
        os.remove(fpath)
    atexit.register(_remove_file, fpath)
    return fpath
