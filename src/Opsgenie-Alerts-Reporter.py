import math
import os
from datetime import datetime
from datetime import timedelta

import configparser
import pytz
import requests

import EmailerPython


# Module information.
__author__ = 'Anthony Farina'
__copyright__ = 'Copyright 2021, Opsgenie Alerts Reporter'
__credits__ = ['Anthony Farina']
__license__ = 'MIT'
__version__ = '1.0.0'
__maintainer__ = 'Anthony Farina'
__email__ = 'farinaanthony96@gmail.com'
__status__ = 'Released'


# Global variables from the config file for easy referencing.
CONFIG = configparser.ConfigParser()
CONFIG_PATH = '/../configs/Opsgenie-Alerts-Reporter-config.ini'
CONFIG.read(os.path.dirname(os.path.realpath(__file__)) + CONFIG_PATH)
OG_API_KEY = CONFIG['Opsgenie API Info']['API-Key']


# This function will calculate the time from last Sunday at 00:00 PST to last Saturday at 23:59:59 PST and
# then will output how many total alerts there were during that time period and how many alerts there were
# that same week during an example set of active hours (09:00 PST - 17:00 PST, Monday - Friday). These
# calculations can be emailed to a specified email address(es) using the Emailer script's configuration.
def opsgenie_alerts_reporter_vitu() -> None:
    # Create a file that will hold the alert report.
    alerts_file = open('alerts.txt', 'w')
    alerts_file.write('Hello!\n\n')

    # Get the date in PST and include it in the report.
    now_pst_dt = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('US/Pacific'))
    alerts_file.write('Today is: ' + datetime.strftime(now_pst_dt, '%m/%d/%Y') + '\n')

    # Get the beginning of last week (Sunday at 00:00 PST) and include it in the report.
    days_to_last_sun_dt = timedelta(((now_pst_dt.weekday() + 1) % 7) + 7)
    sun_last_week_dt = now_pst_dt - days_to_last_sun_dt
    start_last_week_dt = datetime(year=sun_last_week_dt.year, month=sun_last_week_dt.month,
                                  day=sun_last_week_dt.day,
                                  hour=0, minute=0, second=0, tzinfo=now_pst_dt.tzinfo)
    alerts_file.write('The beginning of last week is: ' +
                      str(datetime.strftime(start_last_week_dt, '%m/%d/%Y %H:%M:%S')) + '. ')

    # Make a timestamp for the beginning of last week for the Opsgenie query.
    start_utc_timestamp = math.floor(datetime.timestamp(start_last_week_dt) * 1000)

    # Get the end of last week (Saturday at 23:59 PST) and include it in the report.
    end_last_week_dt = start_last_week_dt + timedelta(days=6, hours=23, minutes=59, seconds=59)
    alerts_file.write('The end of last week is: ' +
                      datetime.strftime(end_last_week_dt, '%m/%d/%Y %H:%M:%S') + '.\n')

    # Make a timestamp for the end of last week for the Opsgenie query.
    end_utc_timestamp = math.floor(datetime.timestamp(end_last_week_dt) * 1000)

    # Prepare and send the API call to OpsGenie.
    og_api_url = 'https://api.opsgenie.com/v2/alerts'
    query_str = 'createdAt>= ' + str(start_utc_timestamp) + \
                ' AND createdAt<= ' + str(end_utc_timestamp)
    og_api_resp = requests.get(url=og_api_url, params={'query': query_str, 'limit': '100'},
                               headers={'Authorization': OG_API_KEY})

    # Convert the API response to JSON. This is the first batch of alerts.
    alerts_batch = og_api_resp.json()

    # Keep track if there are multiple batches of Opsgenie alerts and prepare a list of all alerts.
    next_alert_batch = True
    all_alerts_list = list()

    # Iterate through all alert batches.
    while next_alert_batch:
        # Iterate through the alerts in this alert batch.
        for alert in alerts_batch['data']:
            # Append this alert, regardless of when it was generated.
            all_alerts_list.append(alert)

            # TODO: Add logic here to filter through Opsgenie alerts.

        # Check if there is another batch of alerts.
        if 'next' not in alerts_batch['paging']:
            next_alert_batch = False
        else:
            # Get next alert batch URL ready and send a new Opsgenie API request.
            og_api_url = alerts_batch['paging']['next']
            og_api_resp = requests.get(url=og_api_url, headers={'Authorization': OG_API_KEY})
            alerts_batch = og_api_resp.json()

    # Output the alert data to the alerts file.
    alerts_file.write('\nTotal alerts from last week: ' + str(len(all_alerts_list)))
    alerts_file.close()

    # Run the email script to send the alert data from the alerts file.
    EmailerPython.emailer_python()


# The main method that runs the script. It has no input parameters.
if __name__ == '__main__':
    # Runs the script.
    opsgenie_alerts_reporter_vitu()
