from awsauditor.reportGenerator import ReportGenerator


def main():
    # TODO Grab these from a commandline?
    users = ['lblauvel@ucsc.edu', 'jrbrenna@ucsc.edu', 'jshands@ucsc.edu', 'mkrause1@ucsc.edu', ]
    recipients = ['bvandebr@ucsc.edu']
    start = '2019-01-01'
    end = '2019-01-24'  # Date is inclusive.

    r = ReportGenerator(start_date=start, end_date=end)

    r.send_management_report(recipients)

    for user in users:
        r.send_individual_report(user, recipients)


if __name__ == '__main__':
    main()
