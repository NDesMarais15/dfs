import matplotlib.pyplot as plt
import pandas as pd
from racing_reference_constants import *


racing_data = pd.read_csv('../data/racing_reference2.csv', encoding='latin1', parse_dates=['Date'])


def scatter_by_race(column1, column2):
    for race in racing_data['Race'].unique():
        qualifying_data = racing_data[(racing_data[column1] != -1) & (racing_data[column1] != "-1")
                                      & (racing_data['Race'] == race)].sort_values(column1)
        if qualifying_data.size == 0:
            continue
        plt.scatter(qualifying_data[column1], qualifying_data[column2])
        plt.xlabel(column1)
        plt.ylabel(column2)
        plt.show()


def hist2d(column1, column2):
    filtered_data = racing_data[(racing_data[column1] != -1) & (racing_data[column1] != "-1")]
    plt.hist2d(filtered_data[column1], filtered_data[column2])
    plt.xlabel(column1)
    plt.ylabel(column2)
    plt.show()


def driver_line_graph(driver_name, column):
    filtered_data = racing_data[racing_data[DRIVER] == driver_name].sort_values(DATE)
    plt.plot(filtered_data[DATE], filtered_data[column])
    plt.title(driver_name)
    plt.xlabel(DATE)
    plt.ylabel(column)
    plt.gca().axes.get_xaxis().set_visible(False)
    plt.show()
    pass


hist2d(STARTING_POSITION, FANTASY_POINTS)
