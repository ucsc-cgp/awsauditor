from reportGenerator import ReportGenerator


def main():
    # TODO Grab these from a commandline?
    users = ['user1@email.com', 'email2@email.com' ]
    start = '2019-01-01'
    end = '2019-01-24'  # Date is inclusive.

    managers = {
        'esoth@ucsc.edu': ['toil-dev', 'platform-dev', 'ucsc-cgp-production'], #for cricket
        #'esoth@ucsc.edu': ['platform-hca', 'anvil-dev'],
        #'esoth@ucsc.edu': 'all',
        #'esoth@ucsc.edu': 'all',
        #'esoth@ucsc.edu': ['nanopore-dev'],
        #'esoth@ucsc.edu': ['comparative-genomics-dev'],
    }
    #individuals = ['anovak@soe.ucsc.edu', 'lblauvel@ucsc.edu', 'mbaumann@ucsc.edu', 'mkrause1@ucsc.edu', david, charles,

    for person in managers:
        if managers[person] == 'all':
            r = ReportGenerator(start, end)
        else:
            r = ReportGenerator(start, end, accounts=managers[person])

        r.send_individual_report('mbaumann@ucsc.edu', recipients=['esoth@ucsc.edu'])
        r.send_management_report(person)


if __name__ == '__main__':
    main()
