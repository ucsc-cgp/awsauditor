import csv
import datetime

class Entry:
    """A class for holding data from each row in a bill."""
    def __init__(self, row):
        self.data = row

    @property
    def total(self):
        """Some line items will have a their total cost under the  with the total cost while some have it under TotalCost."""
        today = '"{}"'.format(datetime.date.today())
        return self.data[today] if today in self.data else self.data['"TotalCost"']

    @property
    def id(self):
        return self.data['"RecordID"']

    @property
    def account(self):
        return self.data['"LinkedAccountName"']

    @property
    def service(self):
        return self.data['"ProductCode"']

    @property
    def owner(self):
        return self.data['"user:Owner"']

    @property
    def region(self):
        return self.data['"AvailabilityZone"']

class Bill:
    """A class for managing aws-cost-allocation bills."""
    def __init__(self, sources=None):
        """
        Create a new bill from a given source.

        :param sources: A path to a .csv, a Bill or a list of Bill objects to be merged.
        """
        self.entries = list()
        self.field_names = ''

        if isinstance(sources, str):
            self.importCSV(sources)
        elif isinstance(sources, Bill):
            self.merge(sources)
        elif isinstance(sources, list):
            for bill in sources:
                self.merge(bill)

    def filter(self, owners=None, services=None, accounts=None, regions=None, max=None, min=None):
        """
        Create a new Bill object that only includes specific entries.

        :param List owners: The owner's username to be included in the new Bill. (As specified by the 'user:Owner' entry in the .csv)
        :param List services: The services to be included in the new Bill. (As specified by the 'ProductCode' entry in the .csv)
        :param List accounts: The accounts to be included in the new Bill. (As specified by the 'LinkedAccounts' entry in the .csv)
        :param List regions: The regions to be included in the new Bill. (As specified by the 'AvailabilityZone' entry in the .csv)
        :param max: The maximum cost to be included in the new Bill. (As specified by the 'TotalCost' entry in the .csv)
        :param min: The minimum cost to be included in the new Bill. (As specified by the 'TotalCost' entry in the .csv)
        :return: A new Bill object that contains entries from this instances that match given criteria.
        """
        b = Bill()
        b.entries = self.entries
        b.field_names = self.field_names

        if owners:
            b.entries = [e for e in b.entries if e.owner in owners]
        if services:
            b.entries = [e for e in b.entries if e.service in services]
        if accounts:
            b.entries = [e for e in b.entries if e.account in accounts]
        if regions:
            b.entries = [e for e in b.entries if e.region in regions]
        if max:
            b.entries = [e for e in b.entries if e.total < max]
        if min:
            b.entries = [e for e in b.entries if e.total > min]

        return b

    def merge(self, other_bill):
        """
        Merge this bill with another Bill object.

        The actual functionality of this function has yet to be decided. My initial thoughts are:
            Each line item in the bill has a unique 'RecordID'. To merge a Bill A into Bill B is to take every row in A not
            in B, identified by its RecordID, and put it into B.

        Not sure if this should be a class method that creates a new Bill or modifies the bill calling it.

        :param other_bill: Another Bill object.
        """
        pass

    def export(self, path):
        """
        Exports the data contained in this Bill to a .csv

        All of the entries in the bill generated by AWS are surrounded by "". These must be added to

        :param path: The location where the .csv will be exported to.
        """
        with open(path, 'w') as f:
            f.write(','.join(self.field_names) + '\n')
            for entry in self.entries:
                line = ','.join(['"{}"'.format(v) for v in entry.data.values()])
                f.write(line + '\n')

    def importCSV(self, path):
        """
        Overwrite currently stored data with data from a .csv
        :param path: The path to the source .csv
        """
        with open(path, 'r') as f:
            first_line = f.readline()

            if first_line.startswith('Don\'t see your'):  # AWS generated bills have a message in them, throw it away.
                reader = csv.DictReader(f)
            else:
                line = f.readline().rstrip('\n')
                self.field_names = line.split(',')
                reader = csv.DictReader(f, self.field_names)

            for row in reader:
                self.entries.append(Entry(row))

    def total(self, owners=None, services=None, accounts=None, regions=None):
        """
        Find the total cost spent given a subset of owners, service, and accounts.

        :param owners:
        :param services:
        :param accounts:
        :param regions:
        :return:
        """
        filtered = self.filter(owners, services, accounts, regions)
        return sum([entry.total for entry in filtered.entries])

    @property
    def services(self):
        return {entry.service for entry in self.entries}

    @property
    def owners(self):
        return {entry.owner for entry in self.entries}
