import sys
sys.path.append("..")
from bill import Bill
from awsprinter import awsPrinter
from awsprinter import Category
import argparse
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import datetime
import os

# display the data from a specified history bill
def display_bill():

    # set up command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("bill", help="the source csv file")
    parser.add_argument("--sortOrder", default=None, help="sortOrder=[a, b] sorts output by a, then by b within a")
    parser.add_argument("--owner", default=[], help="If specified, only includes results labelled with this owner")
    parser.add_argument("--zone", default=[], help="If specified, only includes results in this zone e.g. us-west-2a")
    parser.add_argument("--service", default=[], help="If specified, only includes results from this service e.g. AWSDataTransfer")
    parser.add_argument("--tags", default=None, help="If specified, only includes results with this tag in the user:Name field")

    args = vars(parser.parse_args())

    # create bill object from specified path
    bill = Bill(os.path.abspath(args["bill"]))
    for id, entry in bill.entries.items():
        print(entry.owner)

    print("owner: ", args["owner"])
    bill = bill.filter(owners=args["owner"], services=args["service"], regions=["zone"])
    for id, entry in bill.entries.items():
        print(entry.owner)

    #set up default search categories
    zone = Category(bill, "AvailabilityZone", args["zone"])
    username = Category(bill, "user:Owner", args["owner"])
    service = Category(bill, "ProductCode", args["service"])

    now = datetime.datetime.now()

    if args["tags"]:
        print("tags: ", args["tags"])
        bill = awsPrinter.filter_by_tags(bill, args["tags"])

    x_axis = [] # the days to include
    keys = [] # the column titles for each day
    y_axis = [] # the totals for each day

    for day in range(1, now.day):
        key = now.strftime("%Y-%m-") + str(day) # get the column title for each day
        print(key)
        if key in bill.field_names:
            x_axis.append(day)
            keys.append(key)
    print("owner: ", args["owner"])
    print(x_axis)
    print(keys)
    for key in keys:
        total = 0
        for id, entry in bill.entries.items():
            if entry.data[key]: # ignore None entries
                total = total + float(entry.data[key]) # get the sum of all costs for each day
        y_axis.append(total) # add the total to the data set

    print(y_axis)

    axes = plt.axes()
    axes.xaxis.set_major_locator(ticker.MultipleLocator(1)) # set x axis increments to 1 day
    plt.plot(x_axis, y_axis);
    plt.xlabel("date")
    plt.ylabel("total")
    plt.show()


if __name__ == "__main__":
    display_bill()