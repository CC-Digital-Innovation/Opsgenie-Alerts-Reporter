import configparser
import email.utils
import os
import smtplib

from configparser import ExtendedInterpolation
# from email import encoders
# from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# Module information.
__author__ = 'Anthony Farina'
__copyright__ = 'Copyright 2021, Emailer for Python'
__credits__ = ['Anthony Farina']
__license__ = 'MIT'
__version__ = '1.1.2'
__maintainer__ = 'Anthony Farina'
__email__ = 'farinaanthony96@gmail.com'
__status__ = 'Released'


# Prepare the config file reference.
CONFIG = configparser.ConfigParser(interpolation=ExtendedInterpolation())
CONFIG_PATH = '/../configs/Emailer-Python-config.ini'
CONFIG.read(os.path.dirname(os.path.realpath(__file__)) + CONFIG_PATH)

# Prepare SMTP-related variables from the config file.
SMTP_SERVER = CONFIG['SMTP Info']['server']
SMTP_PORT = CONFIG['SMTP Info']['port']
SMTP_USERNAME = CONFIG['SMTP Info']['username']
SMTP_PASSWORD = CONFIG['SMTP Info']['password']

# Prepare party-related variables from the config file.
SENDER = CONFIG['Parties']['sender']
SENDER_NAME = CONFIG['Parties']['sender_name']
RECIPIENTS = CONFIG['Parties']['recipients'].replace('\n', '').split(',')
CC = CONFIG['Parties']['cc'].replace('\n', '').split(',')
BCC = CONFIG['Parties']['bcc'].replace('\n', '').split(',')
ALL_RECIPIENTS = RECIPIENTS + CC + BCC

# Prepare message content variables from the config file.
SUBJECT = CONFIG['Message Contents']['subject']
MSG_BODY = CONFIG['Message Contents']['msg_body'].replace('\\\\n', '\n')
ATTACHMENTS = CONFIG['Message Contents']['attachments'].split(',')


# Sends an email from the sender email address to the recipient email
# address using the SMTP server specified in the config file. The email
# contains a subject, message body, and attachments also specified in the
# config file.
def emailer_python() -> None:
    # Prepare the MIME object for the email.
    message = MIMEMultipart()
    message['Subject'] = SUBJECT
    message['From'] = email.utils.formataddr((SENDER_NAME, SENDER))
    message['To'] = ', '.join(RECIPIENTS)
    message['Cc'] = ', '.join(CC)

    # Attach the message body to the email.
    msg_attachment = MIMEText(get_file_string('./alerts.txt'), 'plain')
    message.attach(msg_attachment)

    # Attach all the files referenced in the config file to the email.
    # for filename in ATTACHMENTS:
    #     # Prepare the file attachment by reading the file as bytes.
    #     file_attachment = MIMEBase('application', 'octet-stream')
    #     file_attachment.set_payload(open(filename, 'rb').read())
    #
    #     # Encode the file attachment in ASCII.
    #     encoders.encode_base64(file_attachment)
    #
    #     # Add the header as a key/value pair to the file attachment.
    #     file_attachment.add_header('Content-Disposition', 'attachment',
    #                                filename=filename)
    #
    #     # Add the file attachment to the email.
    #     message.attach(file_attachment)

    # Try to send the email.
    try:
        # Create SMTP server connection.
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

        # Encrypt the connection via TLS.
        server.ehlo()
        server.starttls()
        server.ehlo()

        # Login and send the email.
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SENDER, ALL_RECIPIENTS, message.as_string())

        # Close the connection to the SMTP server.
        server.close()
    # Print the error to the console in case something goes wrong.
    except Exception as e:
        print("Error: ", e)
    # Print a success message to the console.
    else:
        print("Email sent!")


# Gets the contents of a file in a string for the email's body.
def get_file_string(file_path) -> str:
    # Prepare the return string and open the provided file.
    file_str = ''
    file = open(file_path, 'r')

    # Add each line from the file to the return string.
    for line in file.readlines():
        file_str += line

    # Close the file and return the contents of the file.
    file.close()
    return file_str


# Main method that runs the emailer script.
if __name__ == '__main__':
    # Run the script.
    emailer_python()
