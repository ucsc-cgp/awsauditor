from reportgenerator import ReportGenerator


def main():

    recipients = ['email1@ucsc.edu', 'email2@ucsc.edu']  # TODO Import these from a file?

    # TODO Grab these from a commandline?
    start = '2019-01-01'
    end = '2019-01-09'

    # TODO Might have to use accountID.
    accounts = ['132', '465']

    r = ReportGenerator(start_date=start, end_date=end, accounts=accounts, granularity='DAILY')

    for recipient in recipients:
        r.send_individual_report(recipient)


if __name__ == '__main__':
    main()
