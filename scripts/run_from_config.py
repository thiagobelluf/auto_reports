import argparse
import run_report
import spreadsheet
import utils


def load_config_from_spreadsheet(ss_id):
    f = ss.get_spreadsheet_by_id(ss_id)
    return list(iter_get_spreadsheet_content(f))


def main():
    print ''


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config_spreadsheet_id')
    args = parser.parse_args()
