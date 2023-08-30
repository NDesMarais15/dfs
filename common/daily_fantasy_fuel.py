from importlib import reload
from urllib.error import HTTPError, URLError

from bs4 import BeautifulSoup
import urllib.request
import json
import re
import csv
import datetime

def collect_players(league, date, path):
    url = 'https://www.dailyfantasyfuel.com/%s/projections/draftkings/%s/' % (league, date)

    try:
        fp = urllib.request.urlopen(url)
    except HTTPError as e:
        print(date + ' failed because of ' + e)
        return
    except URLError as e:
        print(date + ' failed because of ' + e)
        return

    my_bytes = fp.read()

    my_str = my_bytes.decode('utf8')
    fp.close()

    soup = BeautifulSoup(my_str, 'html.parser')
    with open(path + '%s projections.csv' % date, 'w+', newline='') as players_csv:
        csv_writer = csv.writer(players_csv, delimiter=',', quotechar='"')

        # Write column headers
        csv_writer.writerow(['Player_Name', 'Salary', 'Team', 'Pos', 'Opp', 'Proj_FP', 'pown%'])

        for tr in soup.find_all('tr', class_='projections-listing'):
            try:
                csv_writer.writerow([
                    tr['data-name'],
                    tr['data-salary'],
                    tr['data-team'],
                    tr['data-pos'],
                    tr['data-opp'],
                    tr['data-ppg_proj'],
                    ''])
            except KeyError:
                print('Could not get info for %s' %  tr['data-name'])
