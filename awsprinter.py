import csv
from collections import OrderedDict
import sys


"""
things to fix:
- combine synonymous usernames e.g. Lon and lblauvel
- have consistent column sizing
- more flexibility in output format
- don't include empty categories in output
"""

# a category by which to search a bill
class Category:
    csvColumn = "" # the name of the column in the bill file, e.g. "user:Owner"
    items = [] # the names in that column to search for

    def __init__(self, bill, name, items=[]):
        self.csvColumn = name
        self.items = items # you can specify a subset of items in the column to search
        if len(self.items) == 0: # or if you don't specify, all unique items are used
            self.items = listAllUniqueItems(bill, name)


# return the dictionary as a multilayered nested dictionary sorted by the given categories
# categories is a list of Category objects, e.g. [services, usernames, accounts]
# layers of the dictionary are in the order given in the list of categories
def sort(dictionary, categories):
    if len(categories) == 0:
        return dictionary # base case

    else:
        output = {name: {} for name in categories[0].items}
        for name in output:
            rowsToAdd = {}
            for key, row in dictionary.items():
                if row[categories[0].csvColumn] == name:
                    rowsToAdd[key] = row
            output[name] = sort(rowsToAdd, categories[1:])
        return output


def listAllUniqueItems(bill, column):
    items = []
    with open(bill, "r") as bill_in:
        reader = csv.DictReader(bill_in)
        for row in reader:
            if not row[column] in items:
                items.append(row[column])
    return(items)


def writeToFile(dictionary, out):
    dictionary = OrderedDict(sorted(dictionary.items()))

    for service in dictionary:
        out.write("\n********  " + service + "  ********\n")
        for zone in dictionary[service]:
            if zone == "":
                out.write("    ====  Not Labelled  ====\n")
            else:
                out.write("    ====  " + zone + "  ====\n")
            for name in dictionary[service][zone]:
                if dictionary[service][zone][name]:
                    if name == "":
                        out.write("        ==  No Name  ==\n")
                    else:
                        out.write("        ==  " + name + "  ==\n")
                    for item in dictionary[service][zone][name]:
                        row = dictionary[service][zone][name][item]
                        out.write("            {:<30}   {:<40}   {:<20}\n".format(row["UsageType"],
                                                                                  row["user:Name"],
                                                                                  row["UsageStartDate"]))

def main():
    if len(sys.argv) != 2:
        print("usage: awsprinter.py <bill.csv>")
        sys.exit(1)

    bill = sys.argv[1]

    # make the default search categories
    zones = Category(bill, "AvailabilityZone")
    usernames = Category(bill, "user:Owner")
    services = Category(bill, "ProductCode")

    with open(bill, 'r') as input:
        byRecordId = {}
        reader = csv.DictReader(input)
        for row in reader:
            byRecordId[row["RecordID"]] = row
        sortedBill = sort(byRecordId, [services, zones, usernames])

    out_file = open("out.txt", "w")
    writeToFile(sortedBill, out_file)
    out_file.close()

if __name__ == '__main__':
    main()



        
        
        



