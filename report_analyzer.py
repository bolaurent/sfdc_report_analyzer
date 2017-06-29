#!/usr/local/bin/python3


# https://developer.salesforce.com/docs/atlas.en-us.api_analytics.meta/api_analytics/sforce_analytics_rest_api_getbasic_reportmetadata.htm

import os
import logging
import argparse
import pdb
import json
import config
from dateutil.parser import parse
from progressbar import ProgressBar

import simple_salesforce


from report import Report
from sfdc import SFDC





logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class MyReport(Report):
    stale_date = config.DEFAULT_STALE_DATE

    def is_stale(self):
        """ should this report be archived as stale?
        """
        return parse(self.queryResult['LastRunDate']) < parse(stale_date)

    def is_relevant(self):
        """ is this report affected by the changes in LOB and product Family?
        """
        if self.describe and 'reportMetadata' in self.describe:
            if 'dormant' in self.folder_name.lower():
                return False

            for filter in self.describe['reportMetadata']['reportFilters']:
                if 'Family' in filter['column']:
                    return 'Family'

                if 'Sub_Family__c' in filter['column']:
                    return 'Sub Family'

                if 'Line_of_Business_LOB__c' in filter['column']:
                    return 'Line of Business (LOB)'

            for filter in self.describe['reportMetadata']['crossFilters']:
                for criteria in filter['criteria']:
                    column = criteria['column']
                    if column in ['Family', 'Sub_Family__c']:
                        return column



def init_sfdc(credentials):
    """ given name of credentials file, initialize salesforce connection
    """

    if not os.path.isfile(credentials):
        credentials = os.path.join(os.path.expanduser('~'), credentials)

    salesforce_credentials = json.loads(open(credentials).read())

    username = salesforce_credentials['user']

    if salesforce_credentials['sandbox']:
        username += '.' + salesforce_credentials['sandbox']

    sfdc = SFDC(username=username,
                password=salesforce_credentials['password'],
                security_token=salesforce_credentials['token'],
                sandbox=salesforce_credentials['sandbox'],
                version=config.DEFAULT_API_VERSION)

    return sfdc

def get_credentials(args):
    if args.production:
        return config.DEFAULT_SFDC_CONFIGFILE_PRODUCTION

    if args.sandbox:
        return config.DEFAULT_SFDC_CONFIGFILE_SANDBOX

    if args.credentials:
        return args.credentials

    return config.DEFAULT_SFDC_CONFIGFILE_PRODUCTION


def validate_args(parser, args):
    if args.restate and args.stale:
        parser.error('Choose either --restate or --stale; not both')
    if not args.restate and not args.stale:
        parser.error('Choose either --restate or --stale')

    if args.production and args.sandbox:
        parser.error('Choose either --production or --sandbox, not both')


def get_where(parser, args):
    if args.restate:
        # return "where id = '00O20000000nCldEAE'"
        where = [config.WHERE_EXCLUDE_FOLDERS, "lastrundate >= 2016-04-01T00:00:00.000Z"]

    elif args.stale:
        # return "where id in ('00OD00000073ADR', '00O8E000000PMYs')"
        where = [config.WHERE_EXCLUDE_FOLDERS, "lastrundate < {}T00:00:00.000Z".format(MyReport.stale_date)]

    if args.where:
        where.append(args.where)

    return where


def handle_args():
    parser = argparse.ArgumentParser(description='Find salesforce reports')
    parser.add_argument('--stale', action="store_true", default=False)
    parser.add_argument('--restate', action="store_true", default=False)
    parser.add_argument('--archive', type=str)
    parser.add_argument('--credentials', type=str)
    parser.add_argument('--sandbox', action="store_true", default=False)
    parser.add_argument('--production', action="store_true", default=False)
    parser.add_argument('--stale_date', type=str)
    parser.add_argument('--where', type=str)
    args = parser.parse_args()

    validate_args(parser, args)

    return parser, args


def get_archive_folder_id(parser, args, sfdc):
    response = sfdc.query_all("select id from folder where name = '{}'".format(args.archive))
    if response['totalSize'] == 0:
        parser.error("Folder not found: '{}".format(args.archive))

    if response['totalSize'] > 1:
        parser.error("Multiple matching folders found: '{}".format(args.archive))

    return response['records'][0]['Id']


def main():
    (parser, args) = handle_args()

    credentials = get_credentials(args)

    if args.stale_date:
        MyReport.stale_date = args.stale_date


    where = get_where(parser, args)

    sfdc = init_sfdc(credentials)

    if args.archive:
        archive_folder_id = get_archive_folder_id(parser, args, sfdc)


    print(Report.header())
    for record in sfdc.reports(where):
        report = MyReport(sfdc, record)

        try:
            if args.restate:
                relevance = report.is_relevant()
                if relevance:
                    print(report.dump(relevance))
            elif args.stale:
                if report.is_stale:
                    print(report.dump())

                    if args.archive:
                        report.move(archive_folder_id)

        except (simple_salesforce.api.SalesforceRefusedRequest, simple_salesforce.api.SalesforceGeneralError) as e:
            logging.error("Salesforce Exception {} {}".format(report.report_id(), str(e)))

        except json.JSONDecodeError as e:
            # This happens when report date filter is set to custom, but dates are blank/null
            logging.error("JSONDecodeError Exception {} {}".format(report.report_id(), str(e)))


if __name__ == "__main__":
    main()
