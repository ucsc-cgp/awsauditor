import csv
from collections import OrderedDict
import sys
from bill import Bill
from bill import Entry


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


# return the Bill as a multilayered nested dictionary sorted by the given categories
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
    unique_items = []

    for key, entry in bill.entries.items():
        if not entry.data[column] in unique_items:
            unique_items.append(entry.data[column])
    return unique_items


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
                        out.write("            {:<30}   {:<40}   {:<20}\n".format(str(row["UsageType"]),
                                                                                  str(row["user:Name"]),
                                                                                  str(row["UsageStartDate"])))

def main():
    if len(sys.argv) != 2:
        print("usage: awsprinter.py <bill.csv>")
        sys.exit(1)

    bill = Bill(sys.argv[1]) # make a bill object from the source file

    #count = 0
    #for key, val in bill.entries.items():
    #   count += 1

    # make the default search categories
    zones = Category(bill, "AvailabilityZone")
    usernames = Category(bill, "user:Owner")
    services = Category(bill, "ProductCode")


    sortedBill = sort({key: val.data for key, val in bill.entries.items()}, [services, zones, usernames])

    #print(count)
    out_file = open("out.txt", "w")
    writeToFile(sortedBill, out_file)
    out_file.close()

if __name__ == '__main__':
    main()



        
        
        



