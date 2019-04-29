import copy
import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os
import shutil


class GraphGenerator:
    """
    A tool for creating graphs from data generated in a ReportGenerator object.
    """
    def __init__(self):
        pass

    @staticmethod
    def list_data(data, name, start_date, end_date, total=False):
        """
        Convert a dictionary that maps names to their daily costs into a tuple of two lists representing x and y values

        :param dict data: the dictionary containing the specified name and desired data
        :param str name: the name to refer to in the dictionary
        :param str start_date: the start date of the data, in the format YYYY-MM-DD
        :param str end_date: the end date of the data, in the format YYYY-MM-DD
        :param bool total: if set to True, the cost for each day is cumulative, a month-to-date total each day
        :return: tuple in the format ([1, 2, 3, ...], [day 1 cost, day 2 cost, day 3 cost, ...])
                 for the given person
        """
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        day = datetime.timedelta(days=1)
        xvals = []
        yvals = []

        if total:
            for i in range(end_date.day - start_date.day + 1):
                xvals.append(i + 1)
                current_date = (start_date + day * i).strftime("%Y-%m-%d")
                if current_date in data[name]:
                    if len(yvals) == 0:
                        yvals.append(data[name][current_date])
                    else:
                        yvals.append(data[name][current_date] + yvals[-1])
                else:
                    if len(yvals) == 0:
                        yvals.append(0)
                    else:
                        yvals.append(yvals[-1])

        else:
            for i in range(end_date.day - start_date.day + 1):
                xvals.append(i + 1)
                current_date = (start_date + day * i).strftime("%Y-%m-%d")
                if current_date in data[name]:
                    yvals.append(data[name][current_date])
                else:
                    yvals.append(0)

        return xvals, yvals

    @staticmethod
    def merge(dic1, dic2):
        """
        Merge dictionaries by adding the values together

        :param dic1: input dictionary
        :param dic2: input dictionary
        :return: modified dic2
        """

        dic2_copy = copy.deepcopy(dic2)
        for key, val in dic1.items():
            if key in dic2_copy:
                dic2_copy[key] += dic1[key]
            else:
                dic2_copy[key] = dic1[key]
        return dic2_copy

    @staticmethod
    def merge_dictionaries(dic1, dic2):
        """
        Combine two three-layer dictionaries

        :param dic1: input dictionary
        :param dic2: input dictionary
        :return: modified dic2
        """
        dic2_copy = copy.deepcopy(dic2)
        for name in dic1:
            if name in dic2_copy:
                if name in ["Total", "Increase"]:
                    dic2_copy[name] += dic1[name]
                else:
                    for service in dic1[name]:
                        if service in ["Total", "Increase"]:
                            dic2_copy[name][service] += dic1[name][service]
                        else:
                            if service in dic2[name]:
                                dic2_copy[name][service] = GraphGenerator.merge(dic1[name][service], dic2_copy[name][service])
                            else:
                                dic2_copy[name][service] = dic1[name][service]
            else:
                dic2_copy[name] = dic1[name]
        return dic2_copy

    @staticmethod
    def graph_bar(data, title, start_date, end_date, total=False, first=None, dark=True):
        """
        Display a matplotlib bar graph of data.

        :param dict data: dictionary mapping names to lists of their daily costs
        :param str title: title to display above the graph
        :param str start_date: the start date of the data, in the format YYYY-MM-DD
        :param str end_date: the end date of the data, in the format YYYY-MM-DD
        :param bool total: if true, display data as a cumulative total cost each day
        :param str first: if specified, plot this person's data first so it is easier for them to read
        :param bool dark: if true, plot on a dark background
        :return: matplotlib plot
        """

        if dark:
            plt.style.use(os.path.abspath("chalicelib/.matplotlib/elip12.mplstyle"))  # style definition

        plt.figure(figsize=(8, 5))
        axes = plt.axes()
        axes.xaxis.set_major_locator(ticker.MultipleLocator(1))  # set the tick marks to integer values

        # label axes
        plt.xlabel("date")
        plt.ylabel("cost in dollars")
        plt.title(title)

        colors = plt.cm.rainbow(np.linspace(0, 1, len(data)))  # make a unique color for each bar

        # keep track of where the top of each stacked bar is after each iteration
        prev = [0 for i in range(int(start_date[-2:]), int(end_date[-2:]) + 1)]  # each bar starts with a height of 0

        if first:  # if specified, graph this person's data first so it all appears at the bottom and is easier to read
            result = GraphGenerator.list_data(data, first, start_date, end_date, total=total)
            plt.bar(result[0], result[1], bottom=prev, label=first)
            prev = [result[1][i] for i in range(len(prev))]

        counter = 0  # iteration counter to keep track of which color to use
        for name in data:
            if name not in ['Total', 'Increase']:
                if first:
                    if name == first:
                        continue  # if the first person to graph was specified, don't graph their data again
                result = GraphGenerator.list_data(data, name, start_date, end_date, total=total)

                if len(result[0]) == 1:  # if only one bar, specify the x range so it doesn't fill the whole plot
                    axes.set_xlim(0, 2)

                plt.bar(result[0], result[1], bottom=prev, label=name, color=colors[counter])

                # update the value of the height of each stacked bar
                prev = [result[1][i] + prev[i] for i in range(len(prev))]

                counter += 1  # update the iteration counter

        legend = plt.legend(bbox_to_anchor=(0.5, -0.1), loc="upper center")  # place the legend outside the plot

        return plt, legend

    @staticmethod
    def clean():
        """Erase everything in the images directory"""

        if os.path.exists("/tmp/"):
            for folder in os.listdir("/tmp/"):
                shutil.rmtree("/tmp/%s" % folder)
