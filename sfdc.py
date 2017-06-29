import pdb
from collections import OrderedDict
import json
from urllib.parse import urljoin
import simple_salesforce
import config

class SFDC(simple_salesforce.Salesforce):

    # fields to be selected
    report_fields = [
        'Id'
        , 'Name'
        , 'FolderName'
        , 'DeveloperName'
        , 'CreatedDate'
        , 'CreatedBy.Name'
        , 'LastRunDate'
        , 'LastModifiedBy.Name'
        , 'LastModifiedDate'
        , 'LastViewedDate'
        , 'Description'
    ]

    def __init__(self, username=None, password=None, security_token=None,
                 sandbox=False, version=config.DEFAULT_API_VERSION):
        super(SFDC, self).__init__(username=username, password=password,
                                   security_token=security_token,
                                   sandbox=sandbox, version=version)

        self.folder_names_by_id = {}
        for folder in self.query_all("select Id, Name from folder")['records']:
            self.folder_names_by_id[folder['Id']] = folder['Name']


    def describe_report(self, report_id):
        """Describes report with given id
        """
        url = self.base_url + "analytics/reports/{}/describe".format(report_id)
        result = self._call_salesforce('GET', url)
        if result.status_code != 200:
            raise simple_salesforce.SalesforceGeneralError(url,
                                                           'describe',
                                                           result.status_code,
                                                           result.content)
        return result.json(object_pairs_hook=OrderedDict)


    def update_report(self, report_id, data, headers=None):
        """Updates a report using a PATCH to
        `.../analytics/reports/{record_id}`.

        If `raw_response` is false (the default), returns the status code
        returned by Salesforce. Otherwise, return the `requests.Response`
        object.

        Arguments:

        * report_id -- the Id of the report to update
        * data -- a dict of the data to update the SObject from. It will be
                  JSON-encoded before being transmitted.

            see https://developer.salesforce.com/docs/atlas.en-us.api_analytics.meta/api_analytics/sforce_analytics_rest_api_save_report.htm#example_save_report

        """
        result = self._call_salesforce(
            method='PATCH',
            url=self.base_url + "analytics/reports/" + report_id,
            data=json.dumps(data)
        )

        # result.content is the full describe info
        return result.status_code


    def reports(self, where):
        """ produces result of select, as a generator

            where -- the where clause (optionally starting with "where ")
                     or, a list of where clauses (eg ["name = 'foo'", "createddate = this_year"])
        """

        if isinstance(where, list):
            where = ' and '.join(where)

        if not where.lower().startswith('where '):
            where = 'where ' + where

        result = self.query_all("select {} from report {} "\
                                     .format(','.join(self.report_fields), where))
        for record in result['records']:
            yield record
