import appbot
import argparse
import json
import spreadsheet as ss


def download_current_state_spreadsheet(ss_id):
    f = ss.get_spreadsheet_by_id(ss_id)
    tmp_file = utils.make_tmp_file()
    ss.download_spreadsheet_to_file(f, tmp_file)
    return tmp_file, f


def upload_to_spreadsheet(source_file, ss_id):
    f = ss.get_spreadsheet_by_id(ss_id)
    utils.log('[Upload] Uploading content to spreadsheet [%s] [%s]' % (f.metadata['title'], ss_id))
    ss.upload_spreadsheet_from_file(source_file, f)


def merge_contents(new_content, old_content=[]):
    utils.log('[Merging] Merging content from files')
    all_fields = set()

    tmp_file = utils.make_tmp_file()
    output_tmp = open(tmp_file, 'wb')

    def update_merged_content(content):
        for c in content:
            all_fields.update(set(c.keys()))
            output_tmp.write('%s\n' % json.dumps(c))

    update_merged_content(new_content)
    update_merged_content(old_content)
    output_tmp.close()

    output_tmp = open(tmp_file, 'rb')
    template = dict([(k, '') for k in all_fields])
    for c in output_tmp:
        c = c.encode('utf-8')
        c = json.loads(c)
        res = template.copy()
        res.update(c)
        yield res
    output_tmp.close()


def execute_report(report_type, **kwargs):
    utils.log('Fetching content for report [%s]' % report_type)

    if report_type == 'fetch_reviews':
        utils.log('[AppBot] Fetching appbot reviews for app [%s]' % app)
        result = appbot.fetch_reviews(
            kwargs['params']['start_date'],
            kwargs['params']['end_date'],
            kwargs['params']['app'],
            fields=kwargs['fields']
        )

    else:
        utils.log('Unknown report type [%s]' % report_type)
    return result


def update_spreadsheet(result, spreadsheet_id, override=False):
    if override:
        utils.log('Overriding content in spreadsheet, if exists: [%s]' % spreadsheet_id)
        current_fpath, current_ss = None, None
    else:
        utils.log('Retrieving content from spreadsheet, if exists [%s]' % spreadsheet_id)
        current_fpath, current_ss = download_current_state_spreadsheet(spreadsheet_id)

    old_content = utils.load_from_csv_file(current_fpath)
    merged_content = merge_contents(result, old_content)
    merged_file = utils.dump_to_csv_file(merged_content)

    upload_to_spreadsheet(merged_file, destiny_spreadsheet_id)


def main(report_type, destiny_spreadsheet_id, params={}, override=False, fields=[]):
    result = execute_report(report_type, **{'params': params, 'fields': fields})
    update_spreadsheet(result, destiny_spreadsheet_id, override=override)


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('report_type')
    parser.add_argument('destiny_spreadsheet_id')
    parser.add_argument('params', nargs='+',
        help='Can pass more than one parameter, in the formato of <key>:<value>:')
    parser.add_argument('-o', '--override', default=False, action='store_true')
    parser.add_argument('-f', '--fields', default='')
    args = parser.parse_args()

    params = dict([p.split(':') for p in args.params])
    fields = [f for f in args.fields.split(',') if f]

    main(
        args.report_type,
        args.destiny_spreadsheet_id,
        params=params,
        override=args.override,
        fields=fields
    )
