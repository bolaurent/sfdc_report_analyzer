import pdb
from collections import OrderedDict
import simple_salesforce
import config

class SFDC(simple_salesforce.Salesforce):

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


    def describeReport(self, id):
        """Describes report with given id
        """
        url = self.base_url + "analytics/reports/{}/describe".format(id)
        result = self._call_salesforce('GET', url)
        if result.status_code != 200:
            raise simple_salesforce.SalesforceGeneralError(url,
                                                           'describe',
                                                           result.status_code,
                                                           result.content)
        return result.json(object_pairs_hook=OrderedDict)

    def reports(self, whereClause):
        result = self.query_all("select {} from report {} "\
                                     .format(','.join(self.report_fields), whereClause))
        for record in result['records']:
            yield record
