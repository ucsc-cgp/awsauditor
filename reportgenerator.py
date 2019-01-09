import boto3
from collections import defaultdict


class ReportGenerator:
    """
    A tool for creating reports based off of AWS Cost Explorer API responses.

    See the following link for more information about the response and request syntax:
    https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_GetCostAndUsage.html
    """
    def __init__(self, start_date, end_date, accounts=None, granularity='DAILY', metrics=None):
        """

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
        self.metrics = metrics or ['BlendedCost']
        self.client = boto3.client('ce')

    def determine_filters(self, users=None):
        """
        Determine the proper filter for the AWS Cost Explorer API call.

        :param list(str) users: A list of user's email addresses.
        :return dict: The proper filter to be used in the API call.
        """

        users_filter = {'And': [{'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': self.accounts}},
                                   {'Tags': {'Key': 'Owner', 'Values': users}}]}
        no_users_filter = {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': self.accounts}}

        return users_filter if users else no_users_filter

    def api_call(self, users=None):
        """
        Retrieve daily cost information for a specific user broken down by the user and service used.

        :param list(str) users: A list of usernames to collect data on. If unspecified the response will contain data
                                for everyone from the accounts specified in self.accounts.
        :return dict response: The response from the AWS Cost Explorer API. See  for more information.
        """
        response = self.client.get_cost_and_usage(
            Filter=self.determine_filters(users),
            Granularity=self.granularity,
            GroupBy=[
                # The order of the elements of this list matters for ReportGenerator.process_api_response.
                # Owner & service must be at indicies 0 & 1, respectively.
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
                'username1' : {
                    'EC2':
                        {
                            '2018-12-30': 126.45,
                            '2018-12-31': 60.45,
                            'Total': 186.90
                        }, ...,
                    'Total': 326.95
                    },

                'username2' : {
                    'EC2':
                        {
                            '2018-12-30': 365.63,
                            '2018-12-31': 100.00,
                            'Total': 465.63
                        }, ...,
                    'Total': 763.23
                },...,

                'Total': 12345.33

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
        Print a report summarizing all of the data.

        :return dict response: The response.
        """
        response = self.api_call()

    def send_individual_report(self, user):
        """
        Print a report for a given user.

        :param str user: The email address of the user who the report is about.
        """
        response = self.api_call([user])
        processed = self.process_api_response(response)

        print('Report for', user)
        print('\n\tExpendatures from {} to {}:'.format(self.start_date, self.end_date))
        for k, v in processed[user].items():
            if k != 'Total':
                print('\t\t{:40} ${:.2f}'.format(k, v['Total']))

        print('\t\t' + '-' * 75)
        print('\t\t{:40} ${:.2f}'.format('Total', processed['Total']))
        print()
