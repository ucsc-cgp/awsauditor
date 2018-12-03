from __future__ import print_function
import boto3
import botocore
import datetime
from datetime import timedelta
import csv
import calendar
import pprint
from collections import OrderedDict
from bill import Bill, HistoricalBill
import os
import datetime

now = datetime.datetime.now()

BUCKET_NAME = 'ben-imp-exp-test'
KEY = "862902209576-aws-cost-allocation-2018-10.csv"


# this should automatically run every day
def get_bill(bill_name, bucket_name):
    """
    Try to get the specificed bill file from the bucket
    and store it in lambda /tmp/ folder
    """
    resource = boto3.resource('s3')
    client = boto3.client('s3')
    destination = "/tmp/" + bill_name  # store the file in the lambda's tmp folder
    d = timedelta(days=1)

    try:  # try to access the file object
        response = client.get_object(
            Bucket=bucket_name,
            IfModifiedSince=(now - d),  # only if bill has been modified since yesterday
            Key=bill_name)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '304':
            return "The bill has not been modified since yesterday."
            exit()
        elif e.response['Error']['Code'] == 'NoSuchKey':
            return "NoSuchKey"
            exit()
        elif e.response['Error']['Code'] == 'AccessDenied':
            return "AccessDenied"
            exit()
        else:
            raise  # something else went wrong

    try:  # try to download the file
        resource.Bucket(bucket_name).download_file(bill_name, destination)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            return "The bill does not exist."
            exit()
        elif e.response['Error']['Code'] == 'Forbidden':
            return "Forbidden"  # do not have permission to access the file
            exit()
        else:
            raise  # something else went wrong


def export_bill(bill_name, bucket_name):
    """
    Export a bill from the lambda's tmp folder to an s3 bucket
    """
    bill_path = "/tmp/" + bill_name
    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(bill_path, bucket_name, bill_name)


def lambda_handler(event, context):
    date = datetime.date.today()

    bucket = 'ben-imp-exp-test'  # for testing
    billingFile = 'aws-cost-allocation-2018-10.csv'  # .format(date.year, date.month)  # Grab from eric's bucket.
    storageFile = '{}-{}.csv'.format(date.year, date.month)  # Grab from somewhere.
    reportPath = str(date) + '.txt'  # Exported to somewhere.

    # save files from bucket into lambda's tmp folder
    response = get_bill(billingFile, bucket)
    if response != None:
        return response
    else:
        new_bill = Bill("/tmp/" + billingFile)  # Has information from the newly generated bill.
    print("got bill")
    response = get_bill(storageFile, bucket)
    if response == "NoSuchKey":
        historical = HistoricalBill("/tmp/" + billingFile)  # create a new historical bill for the new month
    else:
        historical = HistoricalBill("/tmp/" + storageFile)  # open existing historical bill
    print("got history file")
    names = new_bill.owners
    services = new_bill.services
    accounts = new_bill.accounts

    with open("/tmp/" + reportPath, 'w') as f:
        f.write('By Person\n')
        for name in sorted(names):
            before_today = historical.filter(name, services, accounts)  # Grab data for this person from yesterday
            today = new_bill.filter(name, services, accounts)  # From today.
            t = today.total()
            bt = before_today.total()
            increase = t - bt

            # Mention if increase was too small or none at all.
            if increase:
                if round(increase, 2):
                    f.write('\t{}:\t${:.2f} up ${:.2f} from yesterday\n'.format(name, today.total(), increase))
                else:
                    f.write('\t{}:\t${:.2f} up < $0.01 from yesterday\n'.format(name, today.total()))
            else:
                f.write('\t{}:\t${:.2f} No Change\n'.format(name, today.total(), increase))

            for service in sorted(today.services):
                today_cost = today.total(services=service)
                yesterday_cost = before_today.total(services=service, date=date)
                service_increase = today_cost - yesterday_cost

                # Mention if increase was too small or none at all.
                if service_increase:
                    if round(service_increase, 2):
                        f.write('\t\t{}:\t${:.2f} up ${:.2f} from yesterday\n'.format(service, today_cost,
                                                                                      service_increase))
                    else:
                        f.write('\t\t{}:\t${:.2f} up < $0.01 from yesterday\n'.format(service, today_cost))
                else:
                    f.write('\t\t{}:\t${:.2f} No Change\n'.format(service, today_cost, service_increase))
            f.write('\n')

    historical.updateTotals(new_bill, date)  # Update historical with new data.
    historical.export("/tmp/" + storageFile)  # Save updated history to csv in lambda's tmp folder

    export_bill(storageFile, bucket)  # Export history from lambda to bucket.
    export_bill(reportPath, bucket)  # Export report from lambda to bucket

