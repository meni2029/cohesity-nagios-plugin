#!/usr/bin/env python

# Copyright 2019 Cohesity Inc.


"""
check_cohesity_alerts.py
This script looks at alerts and if there are warnings or severe status' raises an alert
else if just info everything is OK

Requires the following non-core Python modules:
- nagiosplugin
- cohesity/app-sdk-python

Change the execution rights of the program to allow the execution to 'all' (usually chmod 0755).
Created by Christina Mudarth
"""



import datetime
import os
from cohesity_management_sdk.cohesity_client import CohesityClient
import argparse
from cohesity_management_sdk.models.alert_state_list_enum import AlertStateListEnum
from cohesity_management_sdk.models.alert_severity_list_enum import AlertSeverityListEnum
from cohesity_management_sdk.models.alert_category_list_enum import AlertCategoryListEnum
import argparse
import logging
import nagiosplugin
import urllib3


CLUSTER_USERNAME = 'admin'
CLUSTER_PASSWORD = 'admin'
CLUSTER_VIP = '10.2.148.30'
DOMAIN = 'LOCAL'


_log = logging.getLogger('nagiosplugin')

class Cohesityalerts(nagiosplugin.Resource):
    def __init__(self, ip, user, password):
        """
        Method to initialize
        :param ip(str): ip address.
        :param user(str): username.
        :param password(str): password.
        """
        self.ip = ip 
        self.user = user
        self.password= password 
        self.cohesity_client = CohesityClient(cluster_vip= CLUSTER_VIP,
                                     username=CLUSTER_USERNAME,
                                     password=CLUSTER_PASSWORD,
                     domain=DOMAIN)
    @property
    def name(self):
        return 'cohesity_ALERT_STATUS'
  
    def get_alerts(self):
        """
        Method to get the cohesity status if critical
        :return: alert_list(lst): all the alerts that are critical or warnings
        """
        try: 
            alerts = self.cohesity_client.alerts
            alerts_list = alerts.get_alerts(max_alerts=100,
                                        alert_state_list=AlertStateListEnum.KOPEN )
        except: 
            _log.debug("Cohesity Cluster is not active")

        alerts_list1 = []
        alerts_list2 = []
        for r in alerts_list: 
                if r.severity == "kCritical":
                    alerts_list1.append("critical")
        for r in alerts_list: 
                if r.severity == "kWarning":
                    alerts_list2.append("warning")
        cc = len(alerts_list1)
        ww = len(alerts_list2)
        return [cc,ww]
     

    def probe(self):
        """
        Method to get the status
        :return: metric(str): nagios status.
        """
        size = self.get_alerts()
        critical = size[0]
        warning = size[1]
        combined = critical + warning

        if critical > 0 or warning > 0:
            _log.debug('There are ' + str(critical) + ' alerts in critical status and ' + str(warning) + ' alerts in warning status')
        else:
            _log.info('All alerts are in info status or no alerts exist')

        metric = nagiosplugin.Metric('Alerts with issues', combined, min=0, context='warning/critical')
        return metric


def parse_args():
    argp = argparse.ArgumentParser()
    argp.add_argument('-s', '--cohesity_client', help="cohesity ip address, username, and password")
    argp.add_argument('-i', '--ip', help="cohesity ip address")
    argp.add_argument('-u', '--user', help="cohesity username")
    argp.add_argument('-p', '--password', help="cohesity password")
    argp.add_argument('-w', '--warning', metavar='RANGE', default='~:0', help='return warning if occupancy is outside RANGE')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='~:0', help='return critical if occupancy is outside RANGE')
    argp.add_argument('-v', '--verbose', action='count', default=0,
                      help='increase output verbosity (use up to 3 times)')
    argp.add_argument('-t', '--timeout', default=30,
                      help='abort execution after TIMEOUT seconds')
    return argp.parse_args()





@nagiosplugin.guarded
def main():


    args = parse_args()
    check = nagiosplugin.Check( Cohesityalerts(args.ip, args.user, args.password) )
    check.add(nagiosplugin.ScalarContext('warning/critical', args.warning, args.critical))
    check.main(args.verbose, args.timeout)

if __name__ == '__main__':
    main()
