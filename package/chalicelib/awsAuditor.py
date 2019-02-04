import datetime
from reportGenerator import ReportGenerator

def main():
    start = str(datetime.date.today().replace(day=1))
    end = str(datetime.date.today())

    manager_accounts = {'casloan@ucsc.edu': ['Toil Dev', 'platform-dev', 'ucsc-cgp-production'],
                        'kosborn2@ucsc.edu': ['platform-hca admin', 'anvil-dev'],
                        'miten@soe.ucsc.edu': ['nanopore-dev'],
                        'markd@ucsc.edu': ['comparative-genomics-dev'],
                        'bpaten@ucsc.edu': [],  # When an RG function recieves an empty list it will default to all accounts.
                        'theathor@ucsc.edu': []}

    users = ["coverbec@ucsc.edu", "jshands@ucsc.edu", "jrbrenna@ucsc.edu", ""]

    r = ReportGenerator(start_date=start, end_date=end)

    # Send account management reports
    #for manager, accounts in manager_accounts.items():
        #r.send_management_report(['bvandebr@ucsc.edu'], accounts)

    # Send individual reports
    for user in users:
        r.send_individual_report(user, recipients=['esoth@ucsc.edu'])

if __name__ == '__main__':
    main()