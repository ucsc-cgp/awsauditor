import unittest
from awsauditor.reportGenerator import ReportGenerator


class ReportGeneratorTest(unittest.TestCase):
    def setUp(self):
        self.sample_response = {'GroupDefinitions': None, 'ResponseMetadata': None,
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

    def testCreateReportBody(self):
        pass

    def testCreateManagementReportBody(self):
        pass

    def testIncrementDate(self):
        """Make sure that incrementing the date works."""
        # Insures end of month and end of year changes.
        end_of_year = '2018-12-31'
        self.assertEqual('2019-01-01', ReportGenerator.increment_date(end_of_year))

        # Insures error handling with invalid dates.
        invalid_date = '2019-01-33'
        with self.assertRaises(ValueError):
            ReportGenerator.increment_date(invalid_date)
