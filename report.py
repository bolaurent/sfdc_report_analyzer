import pdb
from dateutil.parser import parse
import simple_salesforce

from reify import reify

import config


def simplify_dates(strings):
    """ each string in strings arg that appears to be a datetime will be converted to a date
    """
    return [parse(s).date() if s and s.startswith('201') else s for s in strings]

def get(dict, keys):
    """ return list of dict values for given keys
    """
    if not keys:
        return dict

    if not isinstance(keys, list):
        return dict[keys]

    return get(dict[keys.pop(0)], keys)

def quotify(string):
    """ prepare string for export to CSV or tab separated values file
    """
    if not string:
        return ''

    return '"' + str(string).replace('\n', '\\n').replace('"', '\"') + '"'




class Report():
    """ An instance of a report, defined in Salesforce

        methods:

        describe(): return report metadata
        report_id(): return report Id
        report_url(): return report url
        move(): move report to a given folder
        dump(): return a line of text, suitable for output to csv file

    """
    def __init__(self, sfdc, queryResult):
        self.sfdc = sfdc
        self.queryResult = queryResult
        self.folder_name = queryResult['FolderName']

    @reify
    def describe(self):
        """ returns the salesforce definition, as json

            lazy loaded, so we don't waste time calling out to sfdc if we don't need this
        """
        return self.sfdc.describe_report(self.queryResult['Id'])

    def report_id(self):
        """ return Salesforce ID of the report
        """
        return self.queryResult['Id']

    def report_url(self):
        """ Return url that displays the report in UI
        """
        return 'https://{instance}/'.format(instance=self.sfdc.sf_instance) + self.report_id()

    def move(self, folder_id):
        payload = {
            "reportMetadata" : {"folderId":folder_id}
        }
        self.sfdc.update_report(self.report_id(), payload)

    def dump(self, note=''):
        """ return one line, for output to tab-separated-values file
        """

        return('\t'.join([quotify(cell) for cell in [self.folder_name] +

                          [self.describe['reportMetadata']['name']] +

                          simplify_dates([get(self.queryResult, keys) for keys in \
                          [
                              'CreatedDate'
                              , 'LastModifiedDate'
                              , 'LastRunDate'
                              , ['CreatedBy', 'Name']
                              , ['LastModifiedBy', 'Name']
                          ]
                                         ]) +
                          [note] +
                          [self.report_url()]
                         ]))


    @staticmethod
    def header():
        """ return a header line for tab-separated-values file
        """
        return('\t'.join([
            'FolderName'
            , 'Name'
            , 'CreatedDate'
            , 'LastModifiedDate'
            , 'LastRunDate'
            , 'CreatedBy.Name'
            , 'LastModifiedBy.Name'
            , 'Note'
            , 'Url'
        ]))
