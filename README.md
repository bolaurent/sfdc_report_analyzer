NAME
====

**sfdc_report_analyzer** — extracts and prints a list of reports from Salesforce, and optionally moves them to an archive folder


DESCRIPTION
===========



Options
-------

--stale

:   list reports that are stale (older than the stale date, and not already in an archive folder)

--stale_date yyyy-mm--dd

:   reports last viewed before this date will be considered stale. Date must be in ISO format.

--archive "folder name"

: reports listed as stale will be moved to this folder


--restate

:   list reports affected by restatement process (an internal process specific to Canonical)

--sandbox

:   use the Salesforce sandbox, rather than the production instance

--credentials filename

: Get the credentials from this file. The file must be in the current working directory, or be fully qualified, or be in the user's home directory.

--where "name = 'foo'"

: SOQL where clause to limit the reports found


Credentials
-----------

If the --credentials option is not given, credentials are obtained from ~/.sfdc-config.json or (if you add the argument --sandbox) from ~/.sfdc-staging-config.json.


FILES
=====

*~/.sfdc-config.json*

:   user name and credentials for Salesforce production instance

*~/.sfdc-staging-config.json*

:   user name and credentials for Salesforce sandbox instance

The file format is json:
```
    {
      "user":     "me@here.com",
      "password": "mypassword",
      "token":    "ksdfjsdkljsdklj",
      "sandbox":  "staging"
    }
```


AUTHOR
======

Bo Laurent <bo@bolaurent.com>



REFERENCES
==========

* [Salesforce Reports and Dashboards REST API Developer Guide: Save Changes to Reports](https://developer.salesforce.com/docs/atlas.en-us.api_analytics.meta/api_analytics/sforce_analytics_rest_api_save_report.htm#example_save_report
)
