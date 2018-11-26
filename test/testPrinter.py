from awsprinter import awsPrinter
from awsprinter import Category
import os
from bill import Bill
import pprint


def test_sort():
    out_file = open("sort_out.txt", "w")
    # make a bill object from the source file
    bill = Bill(os.path.abspath("862902209576-aws-cost-allocation-2018-10.csv"))

    # make the default search categories
    zones = Category(bill, "AvailabilityZone")
    usernames = Category(bill, "user:Owner")
    services = Category(bill, "ProductCode")

    # make a dictionary of the data from each entry object so it can be sorted
    sorted_bill = awsPrinter.sort({key: val.data for key, val in bill.entries.items()}, [services, zones, usernames])

    awsPrinter.remove_empty_keys(sorted_bill)

    awsPrinter.write_to_file(sorted_bill, out_file)
    out_file.close()


def test_filter():
    out_file = open("filter_out.txt", "w")

    # make a bill only with entries tagged with "redwood"
    bill = Bill(os.path.abspath("862902209576-aws-cost-allocation-2018-10.csv"))
    bill = awsPrinter.filter_by_tags(bill, ["redwood"])

    # make the default search categories
    zones = Category(bill, "AvailabilityZone")
    usernames = Category(bill, "user:Owner")
    services = Category(bill, "ProductCode")

    # make a dictionary of the data from each entry object so it can be sorted
    sorted_bill = awsPrinter.sort({key: val.data for key, val in bill.entries.items()}, [services, zones, usernames])

    awsPrinter.remove_empty_keys(sorted_bill)

    awsPrinter.write_to_file(sorted_bill, out_file)
    out_file.close()


if __name__ == '__main__':
    testSort()
    testFilter()
