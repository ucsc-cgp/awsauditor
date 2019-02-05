import datetime
import boto3
import json
from reportGenerator import ReportGenerator

"""
Send month-to-date account management reports and individualized reports to specified individuals.
"""


def get_recipients(bucket, path):
    """
    Determine the recipients for the management-focused and individual reports.

    The file stored at `path` in `bucket` must have a valid json structure. The dictionary containing info for managers
    must be associated with the 'managers'. The list containing the users to receive reports needs to be associated with
    'users'.

    :param str bucket: the name of the bucket where the recipient info is stored.
    :param str path: The path to the file in 'bucket'.
    :return dict, list: The dictionary that associates managers and the accounts they want reports for and the list of
                        users to receive individual reports.
    """
    s3 = boto3.client('s3')

    file = s3.get_object(Bucket=bucket, Key=path)
    j = json.loads(file['Body'].read())

    return j['managers'], j['users']


def main():
    start = str(datetime.date.today().replace(day=1))
    end = str(datetime.date.today())

    bucket_name = 'bucket-with-file'
    file_name = 'file_in_bucket.json'

    manager_accounts, users = get_recipients(bucket_name, file_name)

    r = ReportGenerator(start_date=start, end_date=end)

    # Send account management reports
    for manager, accounts in manager_accounts.items():
        r.send_management_report([manager], accounts)

    # Send individual reports
    for user in users:
        r.send_individual_report(user)


if __name__ == '__main__':
    main()
