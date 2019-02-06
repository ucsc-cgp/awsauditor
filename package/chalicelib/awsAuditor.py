import datetime
from reportGenerator import ReportGenerator

"""
Send month-to-date account management reports and individualized reports to specified individuals.
"""


def main():
    start = str(datetime.date.today().replace(day=1))
    end = str(datetime.date.today())

    manager_accounts = {'manager1@email.com': ['account1', 'account2'],
                        'manager2@email.com': ['account2', 'account3']}

    users = ['user1@email.com', 'user2@email.com']

    r = ReportGenerator(start_date=start, end_date=end, secret_name="your arn")

    # Send account management reports
    for manager, accounts in manager_accounts.items():
        r.send_management_report(manager, accounts)

    # Send individual reports
    for user in users:
        r.send_individual_report(user)


if __name__ == '__main__':
    main()
