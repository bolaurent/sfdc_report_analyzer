import pdb
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
        return self.sfdc.describeReport(self.queryResult['Id'])

    def report_id(self):
        return self.queryResult['Id']

    def report_url(self):
        return 'https://{instance}/'.format(instance=self.sfdc.sf_instance) + self.report_id()

    def dump(self, note):
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
