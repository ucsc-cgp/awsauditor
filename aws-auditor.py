"""Update running totals from daily, detailed AWS billing csv's and generate a report."""
import csv
import os
import json
import argparse
import datetime

def get_names_and_services_in_raw_data(csv_path, accounts):
    """
    Open the raw csv and create a set of all of the owners of instances and the services being used.
    :param csv_path:
    :param accounts:
    :returns (names,services):
    """
    names = set()
    services = set()
    with open(csv_path, 'r') as f:
        f.readline()  # This file contains a message as its first line and needs to be removed for procecssing.
        reader = csv.DictReader(f)
        for row in reader:
            owner = row['user:Owner'] if row['user:Owner'] and not row['user:Owner'][:2] == 'i-' else 'No Owner'
            service = row['ProductCode']
            account = row['LinkedAccountName']
            if account in accounts and service:
                names.add(owner)
                services.add(service)
    return names, services

def write_report(storage_path, report_path):
    """
    Create a file that breaks down costs by person and by service.

    :param storage_path: The location of the data to write the report with.
    :param report_path: The location where the report should be created.
    """
    with open(storage_path, 'r') as storage_json:
        data = json.load(storage_json)

    with open(report_path, 'w') as report:
        for report_type in data:
            report.write('{}\n'.format(report_type))  # By Person or By Service
            for outer_type in data[report_type]:  # Names or Services
                daily_totals = data[report_type][outer_type]['Total']
                if len(daily_totals) == 1:
                    report.write('\t{}: ${:.2f} first usage this month \n'.format(outer_type, daily_totals[-1]))
                else:
                    total_increase = daily_totals[-1] - daily_totals[-2]
                    if total_increase == 0:
                        report.write('\t{}: ${:.2f} no change \n'.format(outer_type, daily_totals[-1]))
                    elif total_increase < 0.01:
                        report.write('\t{}: ${:.2f} up < $0.01 from yesterday\n'.format(outer_type, daily_totals[-1]))
                    else:
                        report.write('\t{}: ${:.2f} up ${:.2f} from yesterday\n'.format(outer_type, daily_totals[-1], total_increase))

                for inner_type in data[report_type][outer_type]:
                    mtd_values = data[report_type][outer_type][inner_type]
                    if len(mtd_values) == 1:
                        initial_cost = mtd_values[-1]
                        if initial_cost < 0.01:
                            report.write('\t\t{}: < $0.01, first usage this month\n'.format(inner_type))
                        else:
                            report.write('\t\t{}: ${:.2f}, first usage this month\n'.format(inner_type, initial_cost))
                    else:
                        increase = mtd_values[-1] - mtd_values[-2]
                        if increase == 0.0:
                            report.write('\t\t{}: ${:.2f}, no change\n'.format(inner_type, mtd_values[-1]))
                        elif increase < 0.01:
                            report.write('\t\t{}: ${:.2f}, up < $0.01 from yesterday\n'.format(inner_type, mtd_values[-1]))
                        else:
                            report.write('\t\t{}: ${:.2f}, up ${:.2f} from yesterday\n'.format(inner_type, mtd_values[-1], increase))
                report.write('\n')
            report.write('\n')

def digest_csv(path, names, services, accounts):
    """
    Build a dictionary containing daily totals.

    Constructs a nested dictionary pairing People:Services:Cost and Services:People:Cost. ex:
        {'By Person':
            {'Alex': {'EC2': 12.00009, 'S3': 11.03},
            'Sam': {'EC2': 13.04, 'S3': 5.99}},
        'By Service':
            {EC2': {'Alex': 12.00009, 'Sam': 13.04},
            'S3': {'Alex': 11.03, 'Sam': 5.99}}
        }

    :param path: The path to the csv to be digested. (Should be named: [account number]-aws-cost-allocation-[year]-[month].csv)
    :param names: The names of people who are in the csv to be digested. Must be determined beforehand to construct
                  dictionary for tallying totals. (Use get_names_and_services_in_raw_data())
    :param services: Sames as names but services provided by AWS.
    :param accounts: The accounts for which data should be collected.
    :returns dailTotals: A nested dictionary
    """
    dailyTotals = {'By Person': {name: {'Total': 0.0} for name in names},
                   'By Service': {service: {'Total': 0.0} for service in services}}

    # Iterate through the csv and fetch the values for user:Owner (owner, Usually the email address of the person who created it),
    # ProductCode (EC2, S3, ...), and TotalCost (Month to Date, mtd)
    with open(path, 'r') as f:
        f.readline()  # This file contains a message as its first line and needs to be removed for procecssing.
        reader = csv.DictReader(f)
        for row in reader:
            account = row['LinkedAccountName']
            # Owner tags like 'i-0a2754aa8ff2e3f71' are not really helpful, and should not be considered to have an owner.
            owner = row['user:Owner'] if row['user:Owner'] and not row['user:Owner'][:2] == 'i-' else 'No Owner'
            mtd = float(row['TotalCost']) if row['TotalCost'] else 0.0
            service = row['ProductCode']

            if account in accounts and mtd and service:  # Only add to daily total if it was payed for on account of interest.
                ordered_data = [('By Person', owner, service), ('By Service', service, owner)]
                for data in ordered_data:  # Build daily total by person and by service.
                    level = data[0]
                    if data[1] not in dailyTotals[level]:
                        new_entry = {data[1]: {data[2]: mtd, 'Total': mtd}}
                        dailyTotals[level].update(new_entry)
                    elif data[2] not in dailyTotals[level][data[1]]:
                        new_entry = {data[2]: mtd}
                        dailyTotals[level][data[1]].update(new_entry)
                        dailyTotals[level][data[1]]['Total'] += mtd
                    else:
                        dailyTotals[level][data[1]][data[2]] += mtd
                        dailyTotals[level][data[1]]['Total'] += mtd
    return dailyTotals

def digest_csv_to_json(csv_path, json_path, accounts):
    """
    Update the stored data with data from the new billing csv.

    :param csv_path: The path of the csv containing up-to-date month-to-date billing costs.
    :param json_path: The path to the json containing previous month-to-date billing costs.
    :param accounts: A list of accounts that should not be filtered out.
    """
    names, services = get_names_and_services_in_raw_data(csv_path, accounts)

    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            all_data = json.load(f)
    else:
        all_data = {'By Person': {name: dict() for name in names},
                    'By Service': {service: dict() for service in services}}

    dailyTotals = digest_csv(csv_path, names, services, accounts)

    # Update running data with data from the daily report.
    for l1 in dailyTotals:  # 'By Person' or 'By Service'.
        for l2 in dailyTotals[l1]:  # A name or a service.
            if l2 not in all_data[l1]:
                new_name_or_service = {l2: dict()}
                all_data[l1].update(new_name_or_service)
            for l3 in dailyTotals[l1][l2]:  # A service or a name.
                if l3 not in all_data[l1][l2]:
                    new_service = {l3:[dailyTotals[l1][l2][l3]]}
                    all_data[l1][l2].update(new_service)
                else:
                    all_data[l1][l2][l3].append(dailyTotals[l1][l2][l3])

    with open(json_path, 'w') as f:
        json.dump(all_data, f)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--accounts', nargs='*', type=str, default=['Toil Dev', 'platform-dev', 'ucsc-cgp-production'],
                        help='The accounts of interest(as referenced by the "LinkedAccountName" field in a aws-cost-allocation.csv)')
    parser.add_argument('-s', '--storageFile', type=str, required=True,
                        help='The path to the json file containing the historical data.')
    parser.add_argument('-b', '--billingFile', type=str, required=True,
                        help='The path to the .csv file with today\'s billing report.')  # TODO: Pull this from the bucket (Will need to ask for credentials and bucket name)
    parser.add_argument('-o', '--outFile', type=str, default='aws-audit-{}.txt'.format(str(datetime.date.today())),
                        help='The location where the report should be written.')
    parser.add_argument('-c', '--clean', action='store_true',
                        help='Removes the json specified in --storageFile. This will force the creation of a new json.')
    options = parser.parse_args()

    if options.clean:
        os.remove(options.storageFile)
        print('Storage data removed.')
    else:
        digest_csv_to_json(options.billingFile, options.storageFile, options.accounts)
        print('Data updated!')
        write_report(options.storageFile, options.outFile)
        print('Report complete!')

if __name__ == '__main__':
    main()