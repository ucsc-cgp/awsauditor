from awsprinter import awsPrinter
from awsprinter import Category
import os
from bill import Bill
import copy
import pprint

def main():

    bill = Bill(os.path.abspath("862902209576-aws-cost-allocation-2018-10.csv")) # make a bill object from the source file

    #count = 0
    #for key, val in bill.entries.items():
    #   count += 1

    # make the default search categories
    zones = Category(bill, "AvailabilityZone")
    usernames = Category(bill, "user:Owner")
    services = Category(bill, "ProductCode")


    sortedBill = awsPrinter.sort({key: val.data for key, val in bill.entries.items()}, [services, zones, usernames])


    out_file = open("out.txt", "w")
    bill_copy = copy.deepcopy(sortedBill)
    pp = pprint.PrettyPrinter(indent=4)
   # pp.pprint(bill_copy)

    awsPrinter.removeEmptyKeys(bill_copy)
    pp.pprint(bill_copy)
    awsPrinter.writeToFile(bill_copy, out_file)
    out_file.close()

if __name__ == '__main__':
    main()
