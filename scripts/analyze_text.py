import argparse
import atexit
import json
import sys
import utils
from collections import defaultdict


def discover_file_type(fpath):
    return (fpath.endswith('.csv') and 'csv') or 'generic'


def read_input(fpath=None):
    input_parser = lambda i: json.loads(i)

    if fpath:
        file_type = discover_file_type(fpath)

        fh = open(fpath, 'rb')
        close_on_exit = lambda i: i.close()
        atexit.register(close_on_exit, fh)

        if file_type == 'csv':
            reader = csv.DictReader(fh)
            input_parser = lambda i: i
        else:
            reader = fh
    else:
        reader = sys.stdin

    for item in reader:
        yield input_parser(item)


def extract_text_from_content(content, fields):
    return dict([(f, content.get(f)) for f in fields])


def check_contains_terms(text, terms):
    text_parts = set(text.split(' '))
    matches = len(set(terms) - text_parts)
    return matches


def check_not_contains_terms(text, terms):
    text_parts = set(text.split(' '))
    matches = len(text_parts - set(terms))
    return matches


def classify_text(input_content, text_fields, contain_terms, not_contain_terms):
    classification = defaultdict(lambda: defaultdict(int))

    classification['total_inputs_analyzed'] = 0
    for c in input_content:
        classification['total_inputs_analyzed'] += 1

        text_content = extract_text_from_content(c, text_fields)

        for field, text in text_content.items():
            contains = check_contains_terms(text, contain_terms)
            classification[field]['match_contains'] += contains
            classification[field]['count_items_contains'] += 1

            not_contains = check_not_contains_terms(text, not_contain_terms)
            classification[field]['match_not_contains'] += not_contains
            classification[field]['count_items_not_contains'] += 1

            if contains and not not_contains:
                classification[field]['match_terms_filters'] += 1

    return classification


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('contains', help='String containing terms to match. Format: <term_1>,<term_2>,...,<term_n>', default='')
    parser.add_argument('not_contains', help='String containing terms NOT to match. Format: <term_1>,<term_2>,...,<term_n>', default='')
    parser.add_argument('analyzed_fields', help='String containing fields to analyze. Format: <field_1>,<field_2>,...,<field_n>', default='')
    parser.add_argument('-f', '--input_file', default=None)
    args = parser.parse_args()

    content = read_input(fpath=args.input_file)

    parse_string_list = lambda l, d: [i for i in l.split(d) if i]
    contains = parse_string_list(args.contains, ',')
    not_contains = parse_string_list(args.not_contains, ',')
    fields = parse_string_list(args.analyzed_fields, ',')

    counter = classify_text(content, fields, contains, not_contains)
    print json.dumps(counter, indent=4)

