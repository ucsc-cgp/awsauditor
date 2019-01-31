import unittest
from awsauditor.reportGenerator import ReportGenerator


class ReportGeneratorTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.start_date = '2019-01-01'  # TODO Make these the first of the month and today.
        cls.end_date = '2019-01-25'
        cls.username = 'fake_user'
        cls.rg = ReportGenerator(cls.start_date, cls.end_date)

        cls.sample_response = {'GroupDefinitions': None, 'ResponseMetadata': None,
                                'ResultsByTime': [
                                     {'TimePeriod': {'Start': '2019-01-01', 'End': '2019-01-02'},
                                      'Total': dict(),
                                      'Groups': [
                                          {'Keys': ['Owner$user1', 'service1'],
                                           'Metrics': {'BlendedCost': {'Amount': '0.0005', 'Unit': 'USD'}}},
                                          {'Keys': ['Owner$user2', 'service1'],
                                           'Metrics': {'BlendedCost': {'Amount': '0.0005', 'Unit': 'USD'}}},
                                          {'Keys': ['Owner$user2', 'service2'],
                                           'Metrics': {'BlendedCost': {'Amount': '0.0005', 'Unit': 'USD'}}}
                                      ]},
                                     {'TimePeriod': {'Start': '2019-01-02', 'End': '2019-01-03'},
                                      'Total': dict(),
                                      'Groups': [
                                          {'Keys': ['Owner$user1', 'service1'],
                                           'Metrics': {'BlendedCost': {'Amount': '0.0005', 'Unit': 'USD'}}},
                                          {'Keys': ['Owner$user2', 'service1'],
                                           'Metrics': {'BlendedCost': {'Amount': '0.0005', 'Unit': 'USD'}}},
                                          {'Keys': ['Owner$user2', 'service2'],
                                           'Metrics': {'BlendedCost': {'Amount': '0.0005', 'Unit': 'USD'}}}
                                      ]}]
                                }

    def testProcessAPI(self):
        """Ensure that the response returned from the API is reformatted as expected."""

        results = ReportGenerator.process_api_response(self.sample_response)

        expected_results = {
                            'user1': {'service1': {'2019-01-01': 0.0005, '2019-01-02': 0.0005, 'Total': 0.001},
                                      'Total': 0.001},
                            'user2': {'service1': {'2019-01-01': 0.0005, '2019-01-02': 0.0005, 'Total': 0.001},
                                      'service2': {'2019-01-01': 0.0005, '2019-01-02': 0.0005, 'Total': 0.001},
                                      'Total': 0.002},
                            'Total': 0.003
                            }

        self.assertEqual(expected_results, results)

    def testCreateReportBodyNoExpenditures(self):
        """Ensure that an account with no expenditures is treated as such in ReportGenerator.create_report_body()."""
        unused_acct = {'1234': {'Total': 0.0}}

        expected_report = 'Report for {}\n\n\n\tNo expenditures from {} to {}\n\n'.format(self.username, self.start_date, self.end_date)
        generated_report = self.rg.create_report_body(self.username, unused_acct)

        self.assertEqual(expected_report, generated_report)

    def testCreateReportBody(self):
        """Ensure that the report body is generated appropriately in ReportGeneratro.create_report_body()."""
        arbitrary_acct_num, arbitrary_acct_name = next(iter(self.rg.nums_to_aliases.items()))
        acct_expenditures = {'1234': {'Total': 0.0},
                             arbitrary_acct_num: {self.username: {'EC2': {'Total': 56.78}, 'Total': 56.78}, 'Total': 56.78}}

        expected_report = 'Report for {}\n\n\t\t{}\n\t\t\t{:40} ${:.2f}\n'.format(self.username, arbitrary_acct_name, 'EC2', 56.78)
        expected_report += '\t\t\t' + '-' * 47 + '\n'
        expected_report += '\t\t\t{:40} ${:.2f}\n\n'.format('Total', 56.78)
        expected_report += '\t\tExpenditures from {} to {}:  {}\n\n'.format(self.start_date, self.end_date, '$' + str(56.78))

        report = self.rg.create_report_body(self.username, acct_expenditures)

        self.assertNotIn('1234', report)
        self.assertEqual(expected_report, report)

    def testCreateManagementReportBodyNoExpenditures(self):
        """Tests ReportGenerator.create_management_report() effectively catches unused accounts."""

        acct_expenditures = dict()
        for acct_num in self.rg.nums_to_aliases:
            acct_expenditures.update({acct_num: {'Total': 0.0}})

        report = self.rg.create_management_report_body(acct_expenditures)

        # The accounts order of appearance is dictated by the order in which they are taken from the dict in
        # ReportGenerator.create_management_report_body. Consequently, we have to check that each account shows up
        # appropriately in the report.
        for acct_name in self.rg.nums_to_aliases.values():
            acct_report = '\t\t{}\n\t\t\tNo Activity from {} - {}\n\n'.format(acct_name, self.start_date, self.end_date)
            self.assertIn(acct_report, report)

    def testIncrementDate(self):
        """Make sure that incrementing the date works."""
        # Insures end of month and end of year changes.
        end_of_year = '2018-12-31'
        self.assertEqual('2019-01-01', ReportGenerator.increment_date(end_of_year))

        # Insures error handling with invalid dates.
        invalid_date = '2019-01-33'
        with self.assertRaises(ValueError):
            ReportGenerator.increment_date(invalid_date)
