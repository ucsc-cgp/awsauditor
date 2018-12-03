import boto3
import botocore
import datetime
from datetime import timedelta
import csv
import calendar
import pprint
from collections import OrderedDict
from __future__ import print_function

now = datetime.datetime.now()

BUCKET_NAME = 'ben-imp-exp-test'
KEY = "862902209576-aws-cost-allocation-2018-10.csv"
DESTINATION = "new_bill.csv"
BILL_HISTORY = 'new_history.csv'  # 'bill-history-%d-%d.csv' % (now.year, now.month)
BILL = "862902209576-aws-cost-allocation-2018-10.csv"


# this should automatically run every day
def getNewBill():
    resource = boto3.resource('s3')
    client = boto3.client('s3')

    d = timedelta(days=1)

    try:
        response = client.get_object(
            Bucket='ben-imp-exp-test',
            IfModifiedSince=(now - d),  # only if bill has been modified since yesterday
            Key=KEY)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '304':
            print("The bill has not been modified since yesterday.")
            exit()

    try:
        resource.Bucket(BUCKET_NAME).download_file(KEY, DESTINATION)
        print("downloaded bill")
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The bill does not exist.")
            exit()


# this should run on the 1st of each month
def makeNewHistoryFile(file_name):
    # get the number of days in the current month
    daysInMonth = calendar.monthrange(now.year, now.month)[1]
    dayColumns = []
    for i in range(1, daysInMonth + 1):
        dayColumns.append("%d-%d" % (now.month, i))

    # get the field names from the first line of the bill
    with open(KEY, 'r') as file_in:
        file_in.next()
        header = next(csv.reader(file_in))
        header = header + dayColumns  # add a column for each day of the month
        # print(header)

    # copy each row into the new history file
    with open(KEY, 'r') as file_in, open(file_name, 'w') as file_out:
        file_in.next()
        reader = csv.DictReader(file_in)

        writer = csv.DictWriter(file_out, fieldnames=header)

        writer.writeheader()

        for row in reader:
            writer.writerow(row)

    with open(file_name, 'r') as file_out:
        reader = csv.DictReader(file_out)
        # for row in reader:
        # print(row)


# this should belong to the bill class?
def addToHistory(history_file):
    byRecordId = {}

    # get the header to use when writing output
    with open(history_file, 'r') as file_in:
        header = next(csv.reader(file_in))

    with open(KEY, 'r') as bill, open(history_file, 'r+') as history:
        bill.next()  # skip the message in the first line

        billReader = csv.DictReader(bill)
        historyReader = csv.DictReader(history)
        writer = csv.DictWriter(history, fieldnames=header)

        # make a dictionary so each row is accessible by its record id
        for row in historyReader:
            byRecordId[row['RecordID']] = row

        # for each item, add the new day's total to its row in the history
        for row in billReader:
            byRecordId[row['RecordID']]["%d-%d" % (now.month, now.day)] = row['TotalCost']

        # write out the new data
        for key, val in byRecordId.items():
            print(key, val)
            print()
            writer.writerow(val)

if __name__ == "__main__":
    getNewBill()
