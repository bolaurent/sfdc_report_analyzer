#!/usr/local/bin/python3


# https://developer.salesforce.com/docs/atlas.en-us.api_analytics.meta/api_analytics/sforce_analytics_rest_api_getbasic_reportmetadata.htm

import logging
import pdb
import json
from collections import OrderedDict
import config
from progressbar import ProgressBar
from dateutil.parser import *


import simple_salesforce



# queryWhereClause = "where id = '00O20000000nCldEAE'"
queryWhereClause = ""


logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class SFDC(simple_salesforce.Salesforce):
    def __init__(self, username=None, password=None, security_token=None,
                sandbox=False, version=config.DEFAULT_API_VERSION):
        super(SFDC, self).__init__(username=username, password=password, security_token=security_token,
                                    sandbox=sandbox, version=version)


    def describeReport(self, id):
        """Describes report with given id
        """
        url = self.base_url + "analytics/reports/{}/describe".format(id)
        result = self._call_salesforce('GET', url)
        if result.status_code != 200:
            raise SalesforceGeneralError(url,
                                         'describe',
                                         result.status_code,
                                         result.content)
        json_result = result.json(object_pairs_hook=OrderedDict)
        # json_result = result.json()
        if len(json_result) == 0:
            return None
        else:
            return json_result

def init():
    salesforce_credentials = json.loads(open(config.SFDC_CONFIGFILE).read())

    username = salesforce_credentials['user']

    if salesforce_credentials['sandbox']:
        username += '.' + salesforce_credentials['sandbox']
        config.SFDC_URL = 'https://canonical--staging--c.cs87.visual.force.com/'
    else:
        config.SFDC_URL = 'https://eu1.salesforce.com/';

    sfdc = SFDC(username=username,
                      password=salesforce_credentials['password'],
                      security_token=salesforce_credentials['token'],
                      sandbox=salesforce_credentials['sandbox'],
                      version=config.DEFAULT_API_VERSION)

    return sfdc

reportFields = [
    'Id'
    ,'Name'
    # ,'FolderName'
    ,'DeveloperName'
    ,'CreatedDate'
    ,'CreatedBy.Name'
    ,'LastRunDate'
    ,'LastModifiedBy.Name'
    ,'LastModifiedDate'
    ,'LastViewedDate'
    ,'Description'
]


def dumpHeader():
    print('\t'.join([
        'FolderName'
        ,'Name'
        ,'CreatedDate'
        ,'LastModifiedDate'
        ,'LastRunDate'
        ,'CreatedBy.Name'
        ,'LastModifiedBy.Name'
        ,'Note'
        ,'Url'
    ]))

def quotify(s):
    if s == None:
        return ''

    s = str(s)

    if len(s) == 0:
        return ''
    return '"' + s.replace('\n', '\\n').replace('"', '\"') + '"'


def get(dict, keys):
    if not keys:
        return dict

    if not isinstance(keys, list):
        return dict[keys]

    return get(dict[keys.pop(0)], keys)

def simplifyDates(strings):
    retVal = []
    for s in strings:
        if s and s.startswith('201'):
            s = parse(s).date()
        retVal.append(s)
    return retVal


def dumpReport(folderName, reportJson, reportRecord, sfdcUrl, note):
    print('\t'.join([quotify(cell) for cell in [folderName] +

                     [reportJson['reportMetadata']['name']] +

                     simplifyDates([get(reportRecord, keys) for keys in \
                      [
                          'CreatedDate'
                          , 'LastModifiedDate'
                          , 'LastRunDate'
                          , ['CreatedBy', 'Name']
                          , ['LastModifiedBy', 'Name']
                      ]
                     ]) +
                     [note] +
                     [sfdcUrl + reportJson['reportMetadata']['id']]
                    ]))
    pass





def relevant(reportJson):
    if reportJson and 'reportMetadata' in reportJson:
        pdb.set_trace()
        lastRunDate = reportJson['reportMetadata']['LastRunDate']
        if lastRunDate and parse(lastRunDate).date() >= parse('2016-04-01'):
            for filter in reportJson['reportMetadata']['reportFilters']:
                if 'Family' in filter['column']:
                    return 'Family'

                if 'Sub_Family__c' in filter['column']:
                    return 'Sub Family'

                if 'Line_of_Business_LOB__c' in filter['column']:
                    return 'Line of Business (LOB)'

            for filter in reportJson['reportMetadata']['crossFilters']:
                for criteria in filter['criteria']:
                    column = criteria['column']
                    if column in ['Family', 'Sub_Family__c']:
                        return column

    return None


def getFolderName(reportJson, folderNamesById):
    folderId = reportJson['reportMetadata']['folderId']
    folderName = ''
    if folderId in folderNamesById:
        folderName = folderNamesById[folderId]
    elif folderId.startswith('005'):
        folderName = 'My Personal Custom Reports'
    elif folderId.startswith('00D'):
        folderName = 'Unfiled Custom Reports'
    else:
        folderName = folderId

    return folderName


def main():
    sfdc = init()

    sfdcUrl = 'https://{instance}/'.format(instance=sfdc.sf_instance)

    folderNamesById = {}
    for folder in sfdc.query_all("select Id, Name from folder")['records']:
        folderNamesById[folder['Id']] = folder['Name']

    result = sfdc.query_all("select {} from report {} ".format(','.join(reportFields), queryWhereClause))

    dumpHeader()
    progressbar = ProgressBar()
    for reportRecord in progressbar(result['records']):
        reportJson = None
        try:
            reportJson =  sfdc.describeReport(reportRecord['Id'])
        except simple_salesforce.api.SalesforceRefusedRequest as e:
            pass
        except json.JSONDecodeError as e:
            logging.error("JSONDecodeError Exception", reportRecord['Id'], e)
        except Exception as e:
            if e.status == 501:
                pass
            else:
                logging.error("Exception", reportRecord['Id'], str(e), type(e))
                pdb.set_trace()

        relevance = relevant(reportJson)
        if relevance:
            folderName = getFolderName(reportJson, folderNamesById)

            if 'dormant' not in folderName.lower():
                try:
                    dumpReport(folderName, reportJson, reportRecord, sfdcUrl, relevance)
                except Exception as e:
                    logging.error("Exception in dumpReport", reportRecord['Id'], str(e))
                continue



if __name__ == "__main__":
    main()
    pass
