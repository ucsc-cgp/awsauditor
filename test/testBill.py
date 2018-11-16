import unittest
import os
from awsauditor.bill import Bill


class BillTest(unittest.TestCase):
    def testExport(self):
        """Ensure that data from a .csv is exported correctly."""
        pass

    def testPathInitAndExport(self):
        """Test that the init function works."""
        # Paths
        test_data_path = 'data/small_aws_bill.csv'
        exported_bill_path = 'exported_bill.csv'

        # Bill creation and exporting.
        b = Bill(test_data_path)
        b.export(exported_bill_path)

        # Compare the exported csv with the original one.
        with open(test_data_path, 'r') as k:
            k.readline()  # For the sake of comparison, we will not use the message AWS puts in their bill.
            with open(exported_bill_path, 'r') as r:
                for key, result in zip(k, r):
                    self.assertEqual(key, result)

        os.remove(exported_bill_path)

    def testBillInit(self):
        """Ensure that a Bill is initialized properly from another Bill."""
        pass

    def testMultipleBillInit(self):
        """Ensure that multiple bills are merged correctly into a new Bill."""
        pass

    def testFilter(self):
        """Ensure that filtering works."""
        # Things to filter by.
        accounts = ['team2', 'team1']
        owners = ['emp1@ucsc.edu', 'emp2@ucsc.edu']

        # Paths
        test_data_path = 'data/small_aws_bill.csv'
        expected_results_path = 'data/filtered_bill.csv'
        exported_bill_path = 'exported_bill.csv'

        # Bill creation, filtering, and exporting.
        b = Bill(test_data_path)
        f = b.filter(owners=owners, accounts=accounts)
        f.export(exported_bill_path)

        # Compare the exported csv with the expected results.
        with open(expected_results_path, 'r') as k:
            k.readline()  # For the sake of comparison, we will not use the message AWS puts in their bill.
            with open(exported_bill_path, 'r') as r:
                for key, result in zip(k, r):
                    self.assertEqual(key, result)

        os.remove(exported_bill_path)