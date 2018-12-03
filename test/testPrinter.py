import sys
sys.path.append("..")
sys.path.append(".")

import os
from bill import Bill
import pprint

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from awsprinter import awsPrinter
from awsprinter import Category

def test_sort():
    out_file = open("sort_out.txt", "w")

    # make a bill object from the source file
    bill = Bill(os.path.abspath(os.path.join(pkg_root, "test/data/862902209576-aws-cost-allocation-2018-10.csv")))

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
    bill = Bill(os.path.abspath("2018-11.csv"))
    bill = awsPrinter.filter_by_tags(bill, ["dev"])

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
    #test_sort()
    test_filter()
