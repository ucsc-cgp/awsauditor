import boto3
from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
import datetime
import os
from graphGenerator import GraphGenerator


class ReportGenerator:
    """
    A tool for creating reports based off of AWS Cost Explorer API responses.

    See the following link for more information about the response and request syntax and options:
    https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_GetCostAndUsage.html
    """

    def __init__(self, start_date, end_date, accounts=None, granularity='DAILY', metrics=None):
        """
        Create boto3.client and dictionaries that will be used in later functions.

        :param str start_date: The first date of the inquiry. (inclusive)
        :param str end_date: The last date of the inquiry. (exclusive)
        :param list(str) accounts: The accounts for which information will be gathered.
        :param str granularity: The "resolution" of the data. Must be 'DAILY' or 'MONTHLY'.
        :param list(str) metrics: The metrics returned in the query.
        """
        self.start_date = start_date
        self.end_date = end_date

        self.granularity = granularity
        self.metrics = metrics or ['BlendedCost']
        self.client = boto3.client('ce', region_name='us-east-1')  # Region needs to be specified; Cost Explorer hosted here.

        self.nums_to_aliases = self.build_nums_to_aliases(accounts)
        self.account_nums = [num for num in self.nums_to_aliases]
        self.nums_to_aliases["Total"] = "Total"

    @staticmethod
    def increment_date(date):
        """
        Determine the date after a given date

        :param str date: A string representation of a date in the YYYY-MM-DD format.
        :returns: A string representation of a date in the YYYY-MM-DD format.
        """
        y, m, d = [int(x) for x in date.split('-')]

        try:
            day = datetime.datetime(y, m, d)
        except ValueError:
            raise ValueError('Please enter a valid value for end_date when initializing a ReportGenerator.')

        next_day = day + datetime.timedelta(days=1)  # datetime.date does not seem to support this functionality.

        return str(next_day).split(' ')[0]  # return just the date component of the datetime.datetime object.

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

    def determine_groups(self, group_by=None):
        if group_by == "Owner":
            group_list = [
                {
                    'Type': 'TAG',
                    'Key': 'Owner'
                }]
        elif group_by == "Service":
            group_list = [
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        else:
            group_list = [  # The order of the elements of this list matters for ReportGenerator.process_api_response.
                            # Owner & service must be at indices 0 & 1, respectively.
                {
                    'Type': 'TAG',
                    'Key': 'Owner'
                },
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }

            ]
        return group_list

    def api_call(self, users=None, account_nums=None, group_by=None):
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
            GroupBy=self.determine_groups(group_by),
            Metrics=self.metrics,
            TimePeriod={'End': self.increment_date(self.end_date),  # Cost Explorer API's query has an exclusive upper bound.
                        'Start': self.start_date}
        )

        return response

    @staticmethod
    def process_api_response(response, levels=2):
        """
        Turns the response from the AWS Cost Explorer API and turns it into more accessible data.

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


        daily_data = response['ResultsByTime']

        # Use this if the api call was made with group_by BOTH service and owner (for individual reports)
        if levels == 2:  # Create dict with the structure {owner: {service: {date: cost}}}
            processed = defaultdict(lambda: defaultdict(dict))

            for day_dict in daily_data:
                date = day_dict['TimePeriod']['Start']

                services_used = day_dict['Groups']
                for s in services_used:
                    owner = s['Keys'][0].split('$')[1] or 'Untagged'
                    cost = float(s['Metrics']['BlendedCost']['Amount'])
                    if cost >= 0:  # The response contained large negative numbers associated with ''. This rules them out.
                        service = s['Keys'][1]

                        if owner.startswith('i-'):
                            owner = 'i-*'
                            if processed.get(owner) and processed.get(owner).get(service) and processed.get(owner).get(service).get(date):
                                processed[owner][service][date] += cost
                            else:
                                processed[owner][service][date] = cost
                        else:
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

        # Use this if the api call was made with just service OR owner (for management reports)
        elif levels == 1:  # Create dict with the structure {owner: {date: cost}}
            processed = defaultdict(lambda: defaultdict())

            for day_dict in daily_data:
                date = day_dict['TimePeriod']['Start']
                owners = day_dict['Groups']
                for o in owners:
                    if o['Keys'][0].startswith('Owner$'):
                        owner = o['Keys'][0].split('$')[1] or 'Untagged'
                    else:
                        owner = o['Keys'][0] or 'Untagged'

                    cost = float(o['Metrics']['BlendedCost']['Amount'])
                    if cost >= 0:
                        if owner.startswith('i-'):
                            owner = 'i-*'
                            if processed.get(owner) and processed.get(owner).get(date):
                                processed[owner][date] += cost
                            else:
                                processed[owner][date] = cost
                        else:
                            processed[owner][date] = cost

            everyone_total = 0.0
            for owner in processed:
                owner_total = 0.0

                for cost in processed[owner].values():
                    owner_total += cost
                    everyone_total += cost

                processed[owner]['Total'] = owner_total
            processed['Total'] = everyone_total

        return processed

        # TODO Add an 'Previous' total which the day before's total.
        #  This will be helpful in determining how much was spent before the most recent day.

    def create_management_report_body(self, response_by_account):
        """
        Create a string version of the body of the management report.

        The management report will detail how much was spent on each account and by who.

        :param response_by_account: A dictionary containing expenditure data organized by account.
        :return str report: A string containing the report.
        """
        report = '\nReport for ' + ', '.join(self.nums_to_aliases.values()) + '\n'
        report += '\tExpenditures from {} - {}\n\n'.format(self.start_date, self.end_date)

        for acct_num, acct_data in response_by_account.items():
            report += '\t\t{}\n'.format(self.nums_to_aliases[acct_num])

            # If money was spent create a report otherwise indicate no activity.
            if acct_data['Total']:

                # Print total spent for each user
                for user, expenditures in acct_data.items():
                    if user != 'Total':  # The total across all users is stored alongside them and should be ignored.

                        total = expenditures['Total']
                        if total >= 0.01:
                            report += '\t\t\t{:26} ${:.2f}\n'.format(user, total)
                        else:
                            report += '\t\t\t{:26} <$0.01\n'.format(user)

                report += '\t\t\t' + '-' * 34 + '\n'
                report += '\t\t\t{:26} ${:.2f}\n\n'.format('Total', acct_data['Total'])

            else:
                report += '\t\t\tNo Activity from {} - {}\n\n'.format(self.start_date, self.end_date)

        return report

    def create_report_body(self, user, response_by_account):
        """
        Create a string version of a report detailing the expenditures of a user.

        :param user: The email address of the user receiving the report.
        :param response_by_account: A dictionary containing expenditure data organized by account.
        :return str report: A string containing the report.
        """
        spent_money = sum([a['Total'] for a in response_by_account.values()])
        report = 'Report for {}\n\n'.format(user)

        if spent_money:

            # For each account on which money was spent, create a breakdown of expenditures.
            for acct_num, data in response_by_account.items():

                # Only print information for accounts on which money was spent.
                if data['Total']:
                    report += '\t\t{}\n'.format(self.nums_to_aliases[acct_num])

                    # Breakdown by services used.
                    for service, total in data[user].items():
                        if service != 'Total':  # The total across all services is stored alongside them and should be ignored.
                            t = total['Total']
                            report += '\t\t\t{:40} ${:.2f}\n'.format(service, t)

                    report += '\t\t\t' + '-' * 47 + '\n'
                    report += '\t\t\t{:40} ${:.2f}\n\n'.format('Total', data['Total'])

            # TODO fix this string formatting. Using spaces for alignment is janky.
            report += '\t\tExpenditures from {} to {}:  {}\n'.format(self.start_date, self.end_date, '$' + str(round(spent_money, 2)))

        else:
            report += '\n\tNo expenditures from {} to {}\n'.format(self.start_date, self.end_date)

        report += '\n'

        return report

    def send_management_report(self, recipient, clean=True):
        """
        Email a report, tailored to managers, to a list of recipients.

        :param list(str) recipients: The recipients of the email. Defaults to the value of users.
        """
        if not os.path.exists("/tmp/"): # create directory to store graphs in
            os.mkdir("/tmp/")

        if not os.path.exists("/tmp/%s" % recipient):
            os.mkdir("/tmp/%s" % recipient)

        response_by_account = dict()

        # Determine expenditures across all accounts.
        for acct_num in self.account_nums:

            response_by_account[acct_num] = {}
            for category in ['Owner', 'Service']:  # Create a separate report grouped by each of these categories
                response = self.api_call(account_nums=[acct_num], group_by=category)
                processed = self.process_api_response(response, levels=1)
                response_by_account[acct_num][category] = processed

        # Create graphics.
        for acct in response_by_account:
            self.create_account_graphics(response_by_account, recipient, acct)

            # Add in the total field for purposes of making the text report
            response_by_account[acct]['Total'] = max(response_by_account[acct]['Service']['Total'], response_by_account[acct]['Owner']['Total'])

        report = self.create_management_report_body(response_by_account)  # Make the text report

        # Send emails.
        self.send_email(recipient, report, "/tmp/%s" % recipient)

        if clean:
            GraphGenerator.clean()  # delete images once they're used

    def create_account_graphics(self, response_by_account, recipient, acct):
        # Make a graph for this account organized by owner and save it as a png
        plt_by_owner = GraphGenerator.graph_individual(response_by_account[acct]['Owner'],
                                                       "%s Costs This Month By Owner" % self.nums_to_aliases[acct],
                                                       self.start_date, self.end_date)

        plt_by_owner[0].savefig("/tmp/%s/%s_by_owner.png" % (recipient, acct), bbox_extra_artists=(plt_by_owner[1],),
                                bbox_inches='tight', dpi=200)
        plt_by_owner[0].close()

        # Make a graph for this account organized by service and save it as a png
        plt_by_service = GraphGenerator.graph_individual(response_by_account[acct]['Service'],
                                                         "%s Costs This Month By Service" % self.nums_to_aliases[acct]
                                                         , self.start_date, self.end_date)

        plt_by_service[0].savefig("/tmp/%s/%s_by_service.png" % (recipient, acct),
                                  bbox_extra_artists=(plt_by_service[1],),
                                  bbox_inches='tight', dpi=200)
        plt_by_service[0].close()

    def send_individual_report(self, user, recipients=None, clean=True):
        """
        Email a report detailing the expenditures of a given user.

        :param str user: The email address of the user who the report is about.
        :param list(str) recipients: The recipient of the email. If not specified, will default to user.
        :param bool clean: If true, delete the image directory at the end.
        """

        if not os.path.exists("/tmp/"):
            os.mkdir("/tmp/")

        if not os.path.exists("/tmp/%s" % user):  # create directory to store graphs in
            os.mkdir("/tmp/%s" % user)

        recipients = recipients or [user]

        # Determine expenditures for the user across all accounts.
        response_by_account = dict()
        for acct_num in self.account_nums:
            response = self.api_call([user], [acct_num])
            processed = self.process_api_response(response)
            response_by_account[acct_num] = processed

        total = ReportGenerator.sum_dictionary(response_by_account)
        response_by_account["Total"] = total

        # Create graphics.
        for acct in response_by_account:
            if user in response_by_account[acct]:  # create graphical reports
                self.create_individual_graphics(response_by_account, user, acct)

        report = self.create_report_body(user, response_by_account)

        for recipient in recipients:  # Send emails
            self.send_email(recipient, report, "/tmp/%s" % user)  # send the text and graphs together in an email

        if clean:
            GraphGenerator.clean()  # delete images once they're used

    def create_individual_graphics(self, response_by_account, user, acct):
        plt = GraphGenerator.graph_individual(response_by_account[acct][user], "%s's %s Costs This Month"
                                              % (user, self.nums_to_aliases[acct]))
        plt[0].savefig("/tmp/%s/%s.png" % (user, acct), bbox_extra_artists=(plt[1],), bbox_inches='tight', dpi=200)
        plt[0].close()

    @staticmethod
    def sum_dictionary(acct_dic):
        """
        Merge all dictionaries within this dictionary together into a total for all accounts.

        :param acct_dic: input dictionary
        :return: dictionary
        """
        key, value = acct_dic.popitem()
        total = value
        for a in acct_dic:
            total = GraphGenerator.merge_dictionaries(total, acct_dic[a])
        return total

    def send_email(self, recipient, email_body, attachments_path=None):
        """
        Send the report to a recipient.

        :param recipient: the email address to send to
        :param email_body: a string containing the entire email message
        """
        sender = "esoth@ucsc.edu"

        msg = MIMEMultipart()  # set up the email
        msg['Subject'] = 'Your AWS Expenses - from {} - {}'.format(self.start_date, self.end_date)
        msg['From'] = sender
        msg['To'] = recipient

        msg.attach(MIMEText(email_body))

        if attachments_path:
            for png in os.listdir(attachments_path):
                with open(os.path.join(attachments_path, png), 'rb') as p:
                    image = MIMEImage(p.read())
                msg.attach(image)

        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(sender, "@ppleblOss0m")

        text = msg.as_string()

        s.sendmail(sender, recipient, text)
        s.quit()
