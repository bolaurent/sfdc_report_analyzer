#!/usr/local/bin/python3


# https://developer.salesforce.com/docs/atlas.en-us.api_analytics.meta/api_analytics/sforce_analytics_rest_api_getbasic_reportmetadata.htm

import logging
import pdb
import json
import config
from dateutil.parser import parse
from progressbar import ProgressBar

import simple_salesforce


from report import Report
from sfdc import SFDC



# queryWhereClause = "where id = '00O20000000nCldEAE'"
queryWhereClause = "where lastrundate >= 2016-04-01T00:00:00.000Z"


logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


class MyReport(Report):
    def is_stale(self):
        """ should this report be archived as stale?
        """
        return parse(self.queryResult['LastRunDate']) < parse(config.STALE_DATE)

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



def init():
    salesforce_credentials = json.loads(open(config.SFDC_CONFIGFILE).read())

    username = salesforce_credentials['user']

    if salesforce_credentials['sandbox']:
        username += '.' + salesforce_credentials['sandbox']
        config.SFDC_URL = 'https://canonical--staging--c.cs87.visual.force.com/'
    else:
        config.SFDC_URL = 'https://eu1.salesforce.com/'

    sfdc = SFDC(username=username,
                password=salesforce_credentials['password'],
                security_token=salesforce_credentials['token'],
                sandbox=salesforce_credentials['sandbox'],
                version=config.DEFAULT_API_VERSION)

    return sfdc

def main():
    sfdc = init()

    print(Report.header())

    for record in sfdc.reports(queryWhereClause):
        report = MyReport(sfdc, record)
        try:
            relevance = report.is_relevant()
            if relevance:
                print(report.dump(relevance))
        except simple_salesforce.api.SalesforceRefusedRequest as e:
            logging.error("SalesforceRefusedRequest Exception {} {}".format(report.report_id(), str(e)))
        except json.JSONDecodeError as e:
            logging.error("JSONDecodeError Exception {} {}".format(report.report_id(), str(e)))
        except Exception as e:
            logging.error("Exception {} {} {}".format(type(e), report.report_id(), str(e)))


if __name__ == "__main__":
    main()
    pass
