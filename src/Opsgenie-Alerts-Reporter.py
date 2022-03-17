import math
import os
import datetime
from datetime import datetime as dt
from datetime import timedelta

import configparser
import pytz
import requests


# Module information.
__author__ = 'Anthony Farina'
__copyright__ = 'Copyright (c) 2022 Computacenter Digital Innovation'
__credits__ = ['Anthony Farina']
__maintainer__ = 'Anthony Farina'
__email__ = 'farinaanthony96@gmail.com'
__license__ = 'MIT'
__version__ = '2.0.0'
__status__ = 'Released'


# Global config file variables for easy referencing.
CONFIG = configparser.ConfigParser()
CONFIG_PATH = '/../configs/Opsgenie-Alerts-Reporter-config.ini'
CONFIG.read(os.path.dirname(os.path.realpath(__file__)) + CONFIG_PATH)

# Email API global variables.
EMAIL_API_TOKEN = CONFIG['Email Info']['api-token']
EMAIL_API_BASE_URL = 'https://k3s.quokka.ninja/email-api'
EMAIL_API_EMAIL = '/emailReport/'
EMAIL_SUBJECT = CONFIG['Email Info']['subject']
EMAIL_SENDER = 'noreply@quokka.one'
EMAIL_TO = CONFIG['Email Info']['to']
EMAIL_CC = CONFIG['Email Info']['cc']
EMAIL_BCC = CONFIG['Email Info']['bcc']

# Opsgenie global variables.
OG_API_URL = 'https://api.opsgenie.com/v2/'
OG_TIMEZONE = 'UTC'
OG_API_KEY = CONFIG['Opsgenie Info']['API-Key']
OG_ALERT_TAGS = CONFIG['Opsgenie Info']['alert-tags'].split(',')

# Timeframe global variables.
USE_TIMEFRAMES = CONFIG['Timeframes'].getboolean('use-timeframes')
TIMEZONE = CONFIG['Timezone']['timezone']
# Check if the timeframe feature is being used.
if USE_TIMEFRAMES:
    # Represent days of the week in the timeframes as a list of ints.
    DAYS_OF_WEEK = \
        [int(i) for i in CONFIG['Timeframes']['days-of-week'].split(',')]
    # Get the start of the timeframe.
    START_HOUR = CONFIG['Timeframes'].getint('start-hour')
    START_MINUTE = CONFIG['Timeframes'].getint('start-minute')
    START_TIME = datetime.time(hour=START_HOUR, minute=START_MINUTE,
                               tzinfo=pytz.timezone(TIMEZONE))
    # Get the end of the timeframe.
    END_HOUR = CONFIG['Timeframes'].getint('end-hour')
    END_MINUTE = CONFIG['Timeframes'].getint('end-minute')
    END_TIME = datetime.time(hour=END_HOUR, minute=END_MINUTE,
                             tzinfo=pytz.timezone(TIMEZONE))


# This function will gather the total amount of Opsgenie alerts (with
# specific tags) from last Sunday at 00:00 to last Saturday at
# 23:59:59 (relative to when this script runs). On top of that data,
# the user may also enable the timeframe feature to get alerts that
# happened in specific time frames on certain days that same week.
# This report may then be emailed to configurable recipients.
def opsgenie_alerts_reporter() -> None:
    # Create variable to hold the report string.
    report_str = 'Hello!\n\n'

    # Get today's date in the configured timezone and to include in
    # the report.
    now_dt = dt.utcnow().replace(tzinfo=pytz.UTC).astimezone(
        pytz.timezone(TIMEZONE))
    report_str += 'Today is: ' + dt.strftime(now_dt, '%m/%d/%Y %H:%M:%S %Z') \
                  + '\n'

    # Get the beginning of last week (Sunday at 00:00) and include it
    # in the report.
    days_to_last_sun_dt = timedelta(((now_dt.weekday() + 1) % 7) + 7)
    sun_last_week_dt = now_dt - days_to_last_sun_dt
    start_last_week_dt = dt(year=sun_last_week_dt.year,
                            month=sun_last_week_dt.month,
                            day=sun_last_week_dt.day,
                            hour=0, minute=0, second=0, tzinfo=now_dt.tzinfo)
    report_str += 'Last week\'s start: ' + \
                  dt.strftime(start_last_week_dt, '%m/%d/%Y %H:%M:%S %Z') + \
                  '\n'

    # Make a timestamp for the beginning of last week for the Opsgenie
    # query.
    start_utc_timestamp = math.floor(dt.timestamp(start_last_week_dt) * 1000)

    # Get the end of last week (Saturday at 23:59) and include it in
    # the report.
    end_last_week_dt = start_last_week_dt + \
        timedelta(days=6, hours=23, minutes=59, seconds=59)
    report_str += 'Last week\'s end:   ' + \
                  dt.strftime(end_last_week_dt, '%m/%d/%Y %H:%M:%S %Z') + \
                  '\n\n'

    # Make a timestamp for the end of last week for the Opsgenie query.
    end_utc_timestamp = math.floor(dt.timestamp(end_last_week_dt) * 1000)

    # Initialize the query string with timestamp information.
    og_query_str = 'createdAt>= ' + str(start_utc_timestamp) + \
                   ' AND createdAt<= ' + str(end_utc_timestamp)

    # Append all tags to look for in alerts to the query string.
    for tag in OG_ALERT_TAGS:
        og_query_str += ' AND tag: ' + tag

    # Send the API call to OpsGenie.
    og_api_resp = requests.get(url=OG_API_URL + 'alerts',
                               params={'query': og_query_str,
                                       'limit': '100'},
                               headers={'Authorization': OG_API_KEY}
                               )

    # Convert the API response to JSON. This is the first batch of
    # Opsgenie alerts.
    og_alerts_batch = og_api_resp.json()

    # Keep track if there are multiple batches of Opsgenie alerts and
    # prepare a list of all alerts.
    next_og_alert_batch = True
    all_og_alerts_list = list()
    timeframe_og_alerts_list = list()

    # Iterate through all Opsgenie alert batches.
    while next_og_alert_batch:
        # Iterate through the Opsgenie alerts in this alert batch.
        for og_alert in og_alerts_batch['data']:
            # Append this alert, regardless of when it was generated.
            all_og_alerts_list.append(og_alert)

            # Check if we are using the timeframe feature.
            if USE_TIMEFRAMES:
                # Extract the date and time from Opsgenie.
                try:
                    alert_time_dt = dt.strptime(
                        og_alert['createdAt'], '%Y-%m-%dT%H:%M:%S.%fZ')
                except ValueError:
                    alert_time_dt = dt.strptime(
                        og_alert['createdAt'], '%Y-%m-%dT%H:%M:%SZ')

                # Convert the time to the report's timezone.
                alert_time_dt = (alert_time_dt.replace(
                    tzinfo=pytz.timezone(OG_TIMEZONE)).
                    astimezone(pytz.timezone(TIMEZONE)))

                # Check if this alert is not in a configured timeframe.
                in_timeframe = (
                        (START_TIME <= alert_time_dt.time() <= END_TIME)
                        and
                        (alert_time_dt.weekday() in DAYS_OF_WEEK)
                )

                if not in_timeframe:
                    # Move onto the next alert.
                    continue

                timeframe_og_alerts_list.append(og_alert)

        # Check if there is another batch of alerts.
        if 'next' not in og_alerts_batch['paging']:
            next_og_alert_batch = False
        else:
            # Get next alert batch URL ready and send a new Opsgenie
            # API request.
            og_api_resp = requests.get(url=og_alerts_batch['paging']['next'],
                                       headers={'Authorization': OG_API_KEY})
            og_alerts_batch = og_api_resp.json()

    # Output the alert data to the report string.
    report_str += 'Total alerts:   ' + str(len(all_og_alerts_list))

    # Check if we need to include the timeframe numbers in the report.
    if USE_TIMEFRAMES:
        report_str += '\nWorkday alerts: ' + str(len(timeframe_og_alerts_list))

    # Run the email script to send the alert data from the report
    # string.
    print(report_str)
    email_api_resp = requests.post(url=EMAIL_API_BASE_URL + EMAIL_API_EMAIL,
                                   data={
                                       'Token': EMAIL_API_TOKEN,
                                       'ID': 0,
                                       'sender': EMAIL_SENDER,
                                       'subject': EMAIL_SUBJECT,
                                       'to': EMAIL_TO,
                                       'cc': EMAIL_CC,
                                       'bcc': EMAIL_BCC,
                                       'body': report_str,
                                       })
    print(email_api_resp.status_code)
    print(email_api_resp.text)


# The main method that runs the script. It has no input parameters.
if __name__ == '__main__':
    # Runs the script.
    opsgenie_alerts_reporter()
