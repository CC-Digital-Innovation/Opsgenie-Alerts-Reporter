import datetime
import math
import os
from datetime import datetime as dt, timedelta

import configparser
import dotenv
import pytz
import requests


# ====================== Environment / Global Variables =======================
dotenv.load_dotenv(override=True)

# Set up the extraction of global constants from the config file.
CONFIG = configparser.ConfigParser()
CONFIG_PATH = '/../configs/Opsgenie-Alerts-Reporter-config.ini'
CONFIG.read(os.path.dirname(os.path.realpath(__file__)) + CONFIG_PATH)

# Email global constants.
EMAIL_API_BASE_URL = os.getenv('EMAIL_API_BASE_URL')
EMAIL_API_ENDPOINT = os.getenv('EMAIL_API_ENDPOINT')
EMAIL_API_TOKEN = os.getenv('EMAIL_API_TOKEN')
EMAIL_SUBJECT = os.getenv('EMAIL_SUBJECT')
EMAIL_TO = os.getenv('EMAIL_TO')
EMAIL_CC = os.getenv('EMAIL_CC', '')
EMAIL_BCC = os.getenv('EMAIL_BCC', '')
EMAIL_TIME_FORMAT = CONFIG['Email']['time-format']

# Opsgenie global constant variables.
OG_API_ALERTS_URL = os.getenv('OG_API_ALERTS_URL')
OG_API_KEY = os.getenv('OG_API_KEY')
OG_ALERT_TAGS = os.getenv('OG_ALERT_TAGS').split(',')
OG_TIMEZONE = os.getenv('OG_TIMEZONE')

# Timeframe global constant variables.
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


# ================================= Functions =================================
def opsgenie_alerts_reporter() -> None:
    """This function will gather the total amount of Opsgenie alerts (with
    specific tags) from last Sunday at 00:00 to last Saturday at 23:59:59
    (relative to when this script runs). On top of that data, the user may
    also enable the timeframe feature to get alerts that happened in specific
    time frames on certain days that same week. This report may then be
    emailed to configurable recipients."""
    
    # Create variable to hold the report string.
    report_str = 'Hello!\n\n'

    # Get today's date in the configured timezone and to include in
    # the report.
    now = dt.now(pytz.UTC).astimezone(pytz.timezone(TIMEZONE))
    report_str += f'Today is:          ' \
                  f'{dt.strftime(now, EMAIL_TIME_FORMAT)}\n'

    # Get the beginning of last week (Sunday at 00:00) and include it
    # in the report.
    days_to_last_sun_dt = timedelta(((now.weekday() + 1) % 7) + 7)
    sun_last_week_dt = now - days_to_last_sun_dt
    start_last_week_dt = dt(year=sun_last_week_dt.year,
                            month=sun_last_week_dt.month,
                            day=sun_last_week_dt.day,
                            hour=0, minute=0, second=0, tzinfo=now.tzinfo)
    report_str += f'Last week\'s start: ' \
                  f'{dt.strftime(start_last_week_dt, EMAIL_TIME_FORMAT)}\n'

    # Make a timestamp for the beginning of last week for the Opsgenie
    # query.
    start_utc_timestamp = math.floor(dt.timestamp(start_last_week_dt) * 1000)

    # Get the end of last week (Saturday at 23:59) and include it in
    # the report.
    end_last_week_dt = start_last_week_dt + timedelta(days=6, hours=23,
                                                      minutes=59, seconds=59)
    report_str += f'Last week\'s end:   ' \
                  f'{dt.strftime(end_last_week_dt, EMAIL_TIME_FORMAT)}\n\n'

    # Make a timestamp for the end of last week for the Opsgenie query.
    end_utc_timestamp = math.floor(dt.timestamp(end_last_week_dt) * 1000)

    # Initialize the query string with timestamp information.
    og_query_str = f'createdAt>= {start_utc_timestamp} AND createdAt<= ' \
                   f'{end_utc_timestamp}'

    # Append all tags to look for in alerts to the query string.
    for tag in OG_ALERT_TAGS:
        og_query_str += f' AND tag: {tag}'

    # Send the API call to OpsGenie.
    og_api_resp = requests.get(url=OG_API_ALERTS_URL,
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

                # Check if this alert is not in the configured timeframe.
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
    report_str += f'Total alerts:   {len(all_og_alerts_list)}'

    # Check if we need to include the timeframe numbers in the report.
    if USE_TIMEFRAMES:
        report_str += f'\nWorkday alerts: {len(timeframe_og_alerts_list)}'

    # Use the email API to send the report.
    print(report_str)
    email_api_resp = requests.post(url=EMAIL_API_BASE_URL + EMAIL_API_ENDPOINT,
                                   headers={'API_KEY': EMAIL_API_TOKEN},
                                   data={
                                       'subject': EMAIL_SUBJECT,
                                       'to': EMAIL_TO,
                                       'cc': EMAIL_CC,
                                       'bcc': EMAIL_BCC,
                                       'body': report_str,
                                   })
    print(email_api_resp.status_code)
    print(email_api_resp.text)


# ================================ Main Method ================================
if __name__ == '__main__':
    opsgenie_alerts_reporter()
