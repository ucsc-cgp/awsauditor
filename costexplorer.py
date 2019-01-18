import boto3
import copy
import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os
import pprint
import shutil


class CostExplorer:

    @staticmethod
    def get_cost_by(category):
        """
        Using CostExplorer API, get cost data by day
        :param category: the tag to sort by, e.g. 'Owner'
        :return: dictionary of names in the category mapped to a list of the cost for each day
        """
        client = boto3.client('ce')
        now = datetime.datetime.now()

        response = client.get_cost_and_usage(  # retrieve data
            TimePeriod={  # from the first of the month up to today
                'Start': now.strftime("%Y-%m-01"),
                'End': now.strftime("%Y-%m-%d")
            },
            Granularity='DAILY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'TAG',
                    'Key': category
                }
            ]
        )
        #pp = pprint.PrettyPrinter()
        #p.pprint(response)

        data = CostExplorer.condense_response(response)

        return data

    @staticmethod
    def graph_everyone(name=None):
        """
        Make a pyplot stacked bar graph of everyone's costs
        :param name: if specified, plot this person's data first, so it's easier for them to read
        :return: matplotlib plot
        """
        data = CostExplorer.rename_data(CostExplorer.get_cost_by('Owner'))
        plot = CostExplorer.graph_bar(data, "Everyone's costs", first=name)
        return plot

    @staticmethod
    def graph_individual(name, data):
        """
        Make a pyplot stacked bar graph of a specific person's costs split up by service
        :param name: the name to use
        :return: matplotlib plot
        """
        #print(name)
        plot = CostExplorer.graph_bar(data, name + "'s AWS Costs This Month")
        return plot

    @staticmethod
    def get_cost_for_person_by_tag(person):
        """
        Using Cost Explorer API, get costs for a specified person grouped by date and tag
        :param person: Name to filter by
        :return: Dictionary in the format {name: {date: cost}} where name is a string,
                 date is an int, and cost is a float
        """
        client = boto3.client('ce')
        now = datetime.datetime.now()

        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': now.strftime("%Y-%m-01"),
                'End': now.strftime("%Y-%m-%d")
            },
            Granularity='DAILY',
            Filter={
                'Tags': {
                    'Key': 'Owner',
                    'Values': [
                        person
                    ]
                }
            },
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'TAG',
                    'Key': 'Name'
                }
            ]
        )

        condensed = CostExplorer.condense_response(response)
        return condensed

    @staticmethod
    def get_cost_for_person_by_service(person):
        """
        Using Cost Explorer API, get costs for a specified person grouped by date and service
        :param person: Name to filter by
        :return: Dictionary in the format {name: {date: cost}} where name is a string,
                 date is an int, and cost is a float
        """
        client = boto3.client('ce')
        now = datetime.datetime.now()

        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': now.strftime("%Y-%m-01"),
                'End': now.strftime("%Y-%m-%d")
            },
            Granularity='DAILY',
            Filter={
                'Tags': {
                    'Key': 'Owner',
                    'Values': [
                        person
                    ]
                }
            },
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        #print(person)
        #pp = pprint.PrettyPrinter()
        #pp.pprint(response)
        condensed = CostExplorer.condense_response(response)
        return condensed

    @staticmethod
    def graph_bar(data, title, total=False, first=None):
        """
        Display a matplotlib bar graph of data
        :param data: dictionary mapping names to lists of their daily costs
        :param title: title to display above the graph
        :param total: if true, display data as a cumulative total cost each day
        :param first: if specified, plot this person's data first so it is easier for them to read
        :return: matplotlib plot
        """
        plt.style.use("~/elip12.mplstyle")  # style definition

        axes = plt.axes()
        axes.xaxis.set_major_locator(ticker.MultipleLocator(1))  # set the tick marks to integer values
        now = datetime.datetime.now()

        # label axes
        plt.xlabel("date")
        plt.ylabel("cost in dollars")
        plt.title(title)

        colors = plt.cm.rainbow(np.linspace(0, 1, len(data)))  # make a unique color for each bar

        # keep track of where the top of each stacked bar is after each iteration
        prev = [0 for i in range(1, now.day)]  # each bar starts with a height of 0

        if first:  # if specified, graph this person's data first so it all appears at the bottom and is easier to read
            result = CostExplorer.list_data(data, first, total=total)
            plt.bar(result[0], result[1], bottom=prev, label=first)
            prev = [result[1][i] for i in range(len(prev))]

        counter = 0  # iteration counter to keep track of which color to use
        for name in data:
            if first:
                if name == first:
                    continue  # if the first person to graph was specified, don't graph their data again
            result = CostExplorer.list_data(data, name, total=total)

            plt.bar(result[0], result[1], bottom=prev, label=name, color=colors[counter])

            # update the value of the height of each stacked bar
            prev = [result[1][i] + prev[i] for i in range(len(prev))]

            counter += 1  # update the iteration counter

        legend = plt.legend(bbox_to_anchor=(0.5, -0.1), loc="upper center")
        return plt, legend

    @staticmethod
    def graph_stack(data, title, total=False, first=None):
        """
        Return a matplotlib stack plot of data
        :param data: dictionary mapping names to lists of their daily costs
        :param title: title to display above the graph
        :param total: if true, display data as a total cumulative cost each day
        :param first: if specified, plot this person's data first so it is easier for them to read
        :return: matplotlib plot
        """
        plt.style.use("~/elip12.mplstyle")  # style definition

        axes = plt.axes()
        axes.xaxis.set_major_locator(ticker.MultipleLocator(1))  # set the tick marks to integer values

        # label axes
        plt.xlabel("date")
        plt.ylabel("cost")
        plt.title(title)

        y_sets = []
        for name in data:
            result = CostExplorer.list_data(data, name, total=total)
            x = result[0]
            y_sets.append(result[1])
        y = np.vstack(y_sets)  # stack all the y data sets into a 2d array
        plt.stackplot(x, y, label=name)

        plt.legend()
        return plt

    @staticmethod
    def condense_response(data):
        """
        Condense the dictionary returned by the api to just include relevant data
        :param data: api response to condense
        :return: dictionary in the format {name: {date: cost}} where name is a string,
                 date is an int, and cost is a float
        """
        results_by_tag = {}

        for dict in data["ResultsByTime"]:
            date = int(dict["TimePeriod"]["Start"].split("-")[2])  # get the two digit date
            for line in dict["Groups"]:
                total = float(line["Metrics"]["BlendedCost"]["Amount"])  # get the cost

                if '$' in line["Keys"][0]:
                    tag = line["Keys"][0].split("$", 1)[1]  # don't include Name$ or Owner$ at the start
                else:
                    tag = line["Keys"][0]

                if tag in results_by_tag:  # add to an existing entry
                    if date in results_by_tag[tag]:  # there is already a value for this name on this date
                        # add to the existing value (this will only happen to combine names e.g. i- entries)
                        results_by_tag[tag][date] += total
                    else:
                        results_by_tag[tag][date] = total
                else:  # make a new entry
                    results_by_tag[tag] = {date: total}

        return results_by_tag

    @staticmethod
    def switch_names(d, old_name, new_name):
        """
        Rename or combine keys in a dictionary
        :param d: dictionary to use
        :param old_name: key as it currently exists
        :param new_name: key to replace it with
        :return: dictionary with keys replaced
        """
        data = copy.deepcopy(d)
        print(old_name, new_name)
        pp = pprint.PrettyPrinter()
        pp.pprint(data)
        if new_name in data:  # combine keys
            for entry, value in data[old_name].items():
                print(value)
                print(type(value))
                if type(value) is dict:  # 3 layer dictionary
                    if entry in data[new_name]:  # add to already existing value
                        for date in data[old_name][entry].keys():
                            data[new_name][entry][date] += data[old_name][entry][date]
                    else:  # create new value
                        data[new_name][entry] = data[old_name][entry]
                else:  # 2 layer dictionary
                    if entry in data[new_name]:
                        data[new_name][entry] += data[old_name][entry]
                    else:
                        data[new_name][entry] = data[old_name][entry]
        else:  # rename key
            data[new_name] = {}
            for key, val in data[old_name].items():
                data[new_name][key] = val

        data.pop(old_name)  # remove old key once it's copied over

        return data

    @staticmethod
    def rename_data(data):
        """
        Combine i- data into one dictionary and rename blank names to 'unnamed'
        :param data: dictionary to use
        :return: renamed dictionary
        """
        renamed = data
        for tag in data:
            if tag == "":
                renamed = CostExplorer.switch_names(renamed, "", "unnamed")
            elif tag[:2] == "i-":
                renamed = CostExplorer.switch_names(renamed, tag, "i-")
        pp = pprint.PrettyPrinter()
        pp.pprint(renamed)
        return renamed

    @staticmethod
    def list_data(data, name, total=False):
        """
        Convert a dictionary that maps names to their daily costs into
        a tuple of two lists representing x and y values
        :param data: the dictionary containing the specified name and desired data
        :param name: the name to refer to in the dictionary
        :param total: if set to True, the cost for each day is cumulative, a month-to-date total each day
        :return: tuple in the format ([1, 2, 3, ...], [day 1 cost, day 2 cost, day 3 cost, ...])
                 for the given person
        """
        now = datetime.datetime.now()
        xvals = []
        yvals = []

        if total:
            for i in range(1, now.day):
                xvals.append(i)
                if i in data[name]:
                    if len(yvals) == 0:
                        yvals.append(data[name][i])
                    else:
                        yvals.append(data[name][i] + yvals[-1])
                else:
                    if len(yvals) == 0:
                        yvals.append(0)
                    else:
                        yvals.append(yvals[-1])

        else:
            for i in range(1, now.day):
                xvals.append(i)
                if i in data[name]:
                    yvals.append(data[name][i])
                else:
                    yvals.append(0)
        return xvals, yvals

    @staticmethod
    def generate_images():
        """
        Main method
        Generate two png images for each person: a graph of their usage split up by service, and a graph of their usage
        compared to everyone else
        :return: none
        """
        if not os.path.exists("images"):
            os.mkdir("images")

        people = CostExplorer.get_cost_by("Owner")  # get the names of everyone there is data for
        new_data = {}  # dictionary to hold each person's data

        for person in people:
            new_data[person] = CostExplorer.get_cost_for_person_by_service(person)  # make an api call for each person

        new_data = CostExplorer.rename_data(new_data)  # combine names

        for person in new_data:
            if not os.path.exists("images/%s" % person):
                os.mkdir("images/%s" % person)

            plot1 = CostExplorer.graph_everyone(person)
            plot1[0].savefig("images/%s/vs_everyone.png" % person, bbox_extra_artists=(plot1[1],), bbox_inches='tight', dpi=200)
            plot1[0].close()

            plot2 = CostExplorer.graph_individual(person, new_data[person])
            plot2[0].savefig("images/%s/by_tag.png" % person, bbox_extra_artists=(plot1[1],), bbox_inches='tight', dpi=200)
            plot2[0].close()


    @staticmethod
    def clean():
        """
        Erase everything in the images directory
        :return: none
        """
        if os.path.exists("images"):
            shutil.rmtree("images")

