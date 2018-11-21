from collections import OrderedDict
import copy


"""
things to fix:
- combine synonymous usernames e.g. Lon and lblauvel
- have consistent column sizing
- more flexibility in output format
"""

""" a category by which to search a bill """
class Category:
    csvColumn = "" # the name of the column in the bill file, e.g. "user:Owner"
    items = [] # the names in that column to search for



    def __init__(self, bill, name, items=[]):
        self.csvColumn = name
        self.items = items # you can specify a subset of items in the column to search
        if len(self.items) == 0: # or if you don't specify, all unique items are used
            self.items = awsPrinter.listAllUniqueItems(bill, name)


class awsPrinter:

    """ return the Bill as a multilayered nested dictionary sorted by the given categories
    categories is a list of Category objects, e.g. [services, usernames, accounts]
    layers of the dictionary are in the order given in the list of categories """
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
                output[name] = awsPrinter.sort(rowsToAdd, categories[1:])
            return output

    """ make a list of all unique entries in a certain column """
    def listAllUniqueItems(bill, column):
        unique_items = []

        for key, entry in bill.entries.items():
            if not entry.data[column] in unique_items:
                unique_items.append(entry.data[column])
        return unique_items

    """ in progress
    recursive printing function to work with any size/shape of dictionary """
    def writeTo(dictionary, out, indent=""):
        print("writing ", dictionary)
        if type(list(dictionary.values())[0]) is not dict:
            print("here")
            out.write(indent + dictionary["UsageType"] + "\n")
            return

        for key, val in dictionary.items():
            out.write(indent + "==  " + key + "  ==\n")
            awsPrinter.writeTo(val, out, indent + "    ")


    """remove dictionary keys that only contain empty subdictionaries"""
    def removeEmptyKeys(dictionary):
        dict_copy = copy.deepcopy(dictionary)
        is_empty = True
        for key, val in dict_copy.items():
            if type(val) is not dict:
                is_empty = False
                break
            if val:
                response = awsPrinter.removeEmptyKeys(val)
                if response == True:
                    dictionary.pop(key)
                else:
                    is_empty = False
            else:
                dictionary.pop(key)
        return is_empty

    """ format and write out the dictionary """
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

