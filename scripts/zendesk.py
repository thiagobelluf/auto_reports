import argparse
import json
import os
import pytz
import zenpy
import utils
from dateutil import parser as timeparser
from datetime import datetime


DEFAULT_CONFIGS_PATH = './configs'
DEFAULT_CONFIG_FILE = 'zendesk_creds.json'
UTC = pytz.UTC
global CONN
CONN = None


def load_zendesk_credentials(conf_file_path=None):
    conf_file_path = conf_file_path or os.path.join(DEFAULT_CONFIGS_PATH, DEFAULT_CONFIG_FILE)
    with open(conf_file_path, 'rb') as fh:
        return json.load(fh)


def connect(conf_file_path=None):
    global CONN
    if not CONN:
        creds = load_zendesk_credentials()
        CONN = zenpy.Zenpy(**creds)
    return CONN


def parse_ticket(t):
    parse_datetime = lambda dt: datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')

    result = {
        'id': t.id,
        'created_at': parse_datetime(t.created),
        'last_udpated': parse_datetime(t.updated),
        'description': t.description,
        'forum_topic': t.forum_topic,
        'group_name': t.group and t.group.name,
        'user_name': t.requester and t.requester.name,
        'user_email': t.requester and t.requester.email
    }
    return result


def get_all_tickets_created_between(start_date, end_date):
    connect()
    st = timeparser.parse(start_date)
    et = timeparser.parse(end_date)

    total, errors = 0, 0
    try:
        for ticket in CONN.search(order_by='created_at', created_after=st, created_before=et, type='ticket'):
            try:
                yield parse_ticket(ticket)
            except Exception as e:
                utils.log('[ERROR] Could not parse ticket [%s]. Reason: %s' % (ticket.id, e))
                errors += 1
                continue
            total =+ 1
    except Exception as e:
        utils.log('[ERROR] Connection error [%s]' % e)
    utils.log('Found %d tickets for dates [%s] [%s]' % (total, st, et))
    utils.log('Errors: %d (%.2f)'% (errors, total > 0 and 100*(errors/total)))


def _make_file_name(filename_template, *args):
    if '%s' in filename_template:
        filename = filename_template % args
    else:
        filename = filename_template
    return filename


def _datetime_to_date(datetime_str):
    return datetime.strptime(datetime_str, utils.ISO_FMT).strftime('%Y-%m-%d')


if __name__== '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('start_date')
    parser.add_argument('end_date')
    parser.add_argument('--csv', default=False, action='store_true', help='Output items to csv file. Use with --output-file-template option to determine output file name.')
    parser.add_argument('--json', default=False, action='store_true', help='Output items to json file. Use with --output-file-template option to determine output file name.')
    parser.add_argument('-o', '--output-file-template', dest='output_file_template', default='zendesk_tickets_%s.csv',
        help='Template name for the output file. To be used with --csv option. If %s is in the template, it will be replaced by "<start_date>-<end-date>"')
    args = parser.parse_args()

    for s, e in utils.iterate_date(args.start_date, args.end_date):
        utils.log('Getting tickets from zendesk for dates [%s] [%s]' % (s, e))
        tickets = get_all_tickets_created_between(s, e)

        start_end = '%s_%s' % (_datetime_to_date(s), _datetime_to_date(e))
        output_file_name = _make_file_name(args.output_file_template, start_end)

        if args.csv:
            utils.log('Dumping tickets to csv file [%s]' % output_file_name)
            utils.dump_to_csv_file(tickets, output_fpath=output_file_name)
        elif args.json:
            utils.log('Dumping tickets to json file [%s]' % output_file_name)
            utils.dump_to_json_file(tickets, output_fpath=output_file_name)
        else:
            for t in tickets:
                print json.dumps(t)
