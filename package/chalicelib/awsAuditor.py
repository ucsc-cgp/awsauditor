import datetime
from chalicelib.reportGenerator import ReportGenerator

"""
Send month-to-date account management reports and individualized reports to specified individuals.
"""


def main():
    start = str(datetime.date.today().replace(day=1))
    end = str(datetime.date.today())

    manager_accounts = {'esoth@ucsc.edu': ['Toil Dev', 'ucsc-cgp-production']}

    users = ['lblauvel@ucsc.edu', 'mbaumann@ucsc.edu']

    r = ReportGenerator(start_date=start, end_date=end)

    # Send account management reports
    for manager, accounts in manager_accounts.items():
        r.send_management_report(manager, accounts)

    # Send individual reports
    for user in users:
        r.send_individual_report(user, recipients=['esoth@ucsc.edu'])


if __name__ == '__main__':
    main()
