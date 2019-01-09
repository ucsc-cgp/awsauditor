import boto3
from collections import defaultdict


class ReportGenerator:
    """
    A tool for creating reports, individualized by email address, based off of AWS Cost Explorer API responses.

    See https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_GetCostAndUsage.html for more
    information about the response and request syntax.
    """
    def __init__(self, start_date, end_date, accounts=[], granularity='DAILY', metrics=['BlendedCost']):
        """
        Collect data from AWS via Cost Explorer API.

        :param str start_date: The first date of the inquiry. (inclusive)
        :param str end_date: The last date of the inquiry. (exclusive)
        :param list(str) accounts: The accounts for which information will be gathered.
        :param str granularity: The "resolution" of the data. Must be 'DAILY' or 'MONTHLY'.
        :param list(str) metrics: The metrics returned in the query.
        """
        self.start_date = start_date
        self.end_date = end_date
        self.accounts = accounts
        self.granularity = granularity
        self.metrics = metrics
        self.client = boto3.client('ce')

    def individual_api_call(self, users):
        """
        Retrieve daily cost information for a specific user.

        This information is broken down by the user and service used.

        :return dict response: The response from the AWS Cost Explorer API. See  for more information.
        """
        response = self.client.get_cost_and_usage(
            Filter={
                'And': [
                    {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': self.accounts}},
                    {'Tags': {'Key': 'Owner', 'Values': users}}]
            },
            Granularity=self.granularity,
            GroupBy=[  # The order of the elements of this list matters. It is assumed that "service" will be at index 1.
                {
                    'Type': 'TAG',
                    'Key': 'Owner'
                },
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ],
            Metrics=self.metrics,
            TimePeriod={'End': self.end_date,
                        'Start': self.start_date}
        )
        return response

    def everyone_api_call(self):
        response = self.client.get_cost_and_usage(
            Filter={
                'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': self.accounts}
            },
            Granularity=self.granularity,
            GroupBy=[
                {
                    'Type': 'TAG',
                    'Key': 'Owner'
                },
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ],
            Metrics=self.metrics,
            TimePeriod={'End': self.end_date,
                        'Start': self.start_date}
        )
        return response

    def process_api_response(self, response):
        """
        Turns the response from the AWS Cost Explorer API and turns it into more accessable data.

        The returned object is a dictionary of dictionaries that associates a service with a dictionary associating
        dates and costs.

        ex:
            {
                'EC2':
                    {
                        '2018-12-30': 126.45,
                        '2018-12-31': 60.45,
                        'Total': 186.90
                    },

            }

        :param dict response: The response from the AWS Cost Explorer API.
        :returns defaultdict(defaultdict(dict)) processed: Data from the response organized by service:date:cost.
        """
        processed = defaultdict(lambda: defaultdict(dict))

        daily_data = response['ResultsByTime']

        # Create dict associating dates and costs, ordered by service.
        for day_dict in daily_data:
            date = day_dict['TimePeriod']['Start']

            services_used = day_dict['Groups']
            for s in services_used:
                owner = s['Keys'][0].split('$')[1]
                service = s['Keys'][1]
                cost = float(s['Metrics']['BlendedCost']['Amount'])

                processed[owner][service][date] = cost

        # Calculate totals for each owner, service and overall.
        everyone_total = 0.0
        for owner in processed:
            owner_total = 0.0

            for service in processed[owner]:
                service_total = 0.0

                for cost in processed[owner][service].values():
                    service_total += cost
                    owner_total += cost
                    everyone_total += cost

                processed[owner][service]['Total'] = service_total
            processed[owner]['Total'] = owner_total
        processed['Total'] = everyone_total

        return processed


    def send_everyone_report(self):
        """
        Get usage data, grouped by owner, from from the AWS Cost Explorer API call.

        See https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_GetCostAndUsage.html#awscostmanagement-GetCostAndUsage-request-Metrics
        for more detailed information about the request syntax and parameters.

        :return dict response: The response.
        """
        response = self.everyone_api_call()



    def send_individual_report(self, user):
        """


        :param str user: Who the report is about.
        """
        response = self.individual_api_call([user])
        processed = self.process_api_response(response)


        print('Report for', user)
        print('\n\tExpendatures from {} to {}:'.format(self.start_date, self.end_date))
        for k, v in processed[user].items():
            if k != 'Total':
                print('\t\t{:40} ${:.2f}'.format(k, v['Total']))

        print('\t\t' + '-' * 75)
        print('\t\t{:40} ${:.2f}'.format('Total', processed['Total']))
        print()
