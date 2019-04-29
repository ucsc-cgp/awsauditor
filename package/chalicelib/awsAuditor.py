import datetime
import boto3
import json
from chalicelib.reportGenerator import ReportGenerator

"""
Send month-to-date account management reports and individualized reports to specified individuals.
"""


def get_config(bucket, path):
    """
    Determine the config settings.

    The file stored at `path` in `bucket` must have a valid json structure.

    The dictionary containing info for managers must be associated with the 'managers'.
    The list containing the users to receive reports needs to be associated with 'users'.
    The secret name being used to set up emailing in ReportGenerator must be associated with 'secret_name'.

    :param str bucket: the name of the bucket where the recipient info is stored.
    :param str path: The path to the file in 'bucket'.
    :return dict: The dictionary that associates managers and the accounts they want reports for, the list of
                        users to receive individual reports and the secret name being used to configure the email.
    """
    s3 = boto3.client('s3')

    file = s3.get_object(Bucket=bucket, Key=path)
    j = json.loads(file['Body'].read())

    return j


def main():
    start = str(datetime.date.today().replace(day=1))
    end = str(datetime.date.today())

    bucket_name = 'bucketwith-config'
    file_name = 'config.json'

    config = {"managers": {"esoth@ucsc.edu": ["Toil Dev", "platform-dev", "ucsc-cgp-production"]},
              "users": [],
              "secret_name": "awsauditor_email"}

    manager_accounts = config['managers']
    users = config['users']
    secret_name = config['secret_name']

    r = ReportGenerator(start_date=start, end_date=end, secret_name=secret_name)

    # Send account management reports
    for manager, accounts in manager_accounts.items():
        r.send_management_report([manager], accounts)

    # Send individual reports
    for user in users:
        r.send_individual_report(user)


if __name__ == '__main__':
    main()
