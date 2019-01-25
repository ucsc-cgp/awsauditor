from reportGenerator import ReportGenerator


def main():
    # TODO Grab these from a commandline?
    users = ['user1@email.com', 'email2@email.com' ]
    recipients = ['manager@email.edu']
    start = '2019-01-01'
    end = '2019-01-24'  # Date is inclusive.

    r = ReportGenerator(start_date=start, end_date=end)

    r.send_management_report(recipients)

    for user in users:
        r.send_individual_report(user, recipients)


if __name__ == '__main__':
    main()
