import datetime

DEFAULT_API_VERSION = '40.0'
DEFAULT_SFDC_CONFIGFILE_PRODUCTION = '.sfdc-config.json'
DEFAULT_SFDC_CONFIGFILE_SANDBOX = '.sfdc-staging-config.json'

# first day of previous calendar year
DEFAULT_STALE_DATE = "{}-01-01".format(datetime.date.today().year-1)


ARCHIVED_FOLDERNAME_PATTERNS = [
    '%dormant%',
    '%archived%'
]

WHERE_EXCLUDE_FOLDERS = ' and '.join(["(not foldername like '{}')".format(folder) for folder in ARCHIVED_FOLDERNAME_PATTERNS])
