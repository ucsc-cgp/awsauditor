import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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

        self.nums_to_aliases = self.build_nums_to_aliases(accounts)
        self.account_nums = self.nums_to_aliases.keys()

        self.granularity = granularity
        self.metrics = metrics or ['BlendedCost']
        self.client = boto3.client('ce', region_name='us-east-1')  # Region needs to be specified; Cost Explorer hosted here.

    @staticmethod
    def build_nums_to_aliases(aliases=None):
        """
        Create a dictionary that pairs account numbers with their aliases.
        :param aliases: A list of account aliases.
        :return dict: A dictionary that pairs account numbers with their aliases.
        """

        client = boto3.client('organizations')
        response = client.list_accounts()

        if aliases:
            nums_to_aliases = {account['Id']: account['Name'] for account in response['Accounts'] if account['Name'] in aliases}
        else:
            nums_to_aliases = {account['Id']: account['Name'] for account in response['Accounts']}

        return nums_to_aliases

    def determine_filters(self, users=None, account_nums=None):
        """
        A helper function for determining the proper filter for the AWS Cost Explorer API call.
        By default this will return a filter for each user associated with all of the accounts in self.acounts.
        A list of users and accounts can be specified to narrow your search results.
        :param list(str) users: A list of users' email addresses.
        :param list(str) account_nums: A list of the account numbers of interest.
        :return dict: The proper filter to be used in the API call.
        """

        users_filter = {'And': [{'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': account_nums or self.account_nums}},
                                {'Tags': {'Key': 'Owner', 'Values': users}}]}
        no_users_filter = {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': account_nums or self.account_nums}}

        return users_filter if users else no_users_filter

    def api_call(self, users=None, account_nums=None):
        """
        Retrieve daily cost information for a specific user broken down by the user and service used.
        By default this will return information about each user associated with all of the accounts in self.acounts.
        A list of users and accounts can be specified to narrow your search results.
        :param list(str) users: A list of usernames to collect data on. If unspecified the response will contain data
                                for everyone from the accounts specified in self.accounts.
        :param list(str) account_nums: A list of the account numbers of interest. If unspecified the response will contain
                                    data for all of the accounts specified in self.accounts.
        :return dict response: The response from the AWS Cost Explorer API. See  for more information.
        """
        response = self.client.get_cost_and_usage(
            Filter=self.determine_filters(users, account_nums),
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

    @staticmethod
    def process_api_response(response):
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
        pass

    def send_individual_report(self, user):
        """
        Print a report for a given user.
        :param str user: The email address of the user who the report is about.
        """
        # Determine expenditures for the user across all accounts.
        response_by_account = dict()
        for acct_num in self.account_nums:
            response = self.api_call([user], [acct_num])
            processed = self.process_api_response(response)
            response_by_account[acct_num] = processed

        report_string = self.create_report_body(user, response_by_account)

        self.send_email(user, report_string)
        

    def create_report_body(self, user, response_by_account):
        """
        Create a string version of a report detailing the expenditures of a user.
        :param user: The email address of the user recieving the report.
        :param response_by_account: a dictionary containing expenditure data organized by account.
        :return str report: a string containing the report.
        """
        report = 'Report for {}\n'.format(user)

        # Determine if money was spent.
        spent_money = sum([a['Total'] for a in response_by_account.values()])
        if spent_money:
            report += '\n\tExpenditures from {} to {}:\n'.format(self.start_date, self.end_date)

            # For each account on which money was spent, create a breakdown of expenditures.
            for acct_num, data in response_by_account.items():
                if data['Total']:
                    report += '\t\tAccount: {}\n'.format(self.nums_to_aliases[acct_num])

                    # Breakdown by services used.
                    for service, total in data[user].items():
                        if service != 'Total':  # The total across all services is stored alongside them and should be ignored.
                            t = total['Total']
                            report += '\t\t\t{:40} ${:.2f}\n'.format(service, t)

                    report+= '\t\t\t' + '-' * 47 + '\n'
                    report += '\t\t\t{:40} ${:.2f}\n\n'.format('Total', data['Total'])
        else:
            report += '\n\tNo expenditures from {} to {}\n'.format(self.start_date, self.end_date)

        report += '\n'

        return report

def send_email(recipient, email_body):
    """
    Send an email from Emily's address
    :param recipient: the email address to send to
    :param email_body: a string containing the entire email message
    :return: none
    """
    sender = 'esoth@ucsc.edu'

    msg = MIMEMultipart()  # set up the email
    msg['Subject'] = 'Your AWS Expenses'
    msg['From'] = sender
    msg['To'] = recipient

    msg.attach(MIMEText(email_body))

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login('esoth@ucsc.edu', '@ppleblOss0m')

    text = msg.as_string()

    s.sendmail(sender, recipient, text)

    s.quit()


if __name__ == '__main__':
    send_email('esoth@ucsc.edu', "testing")
