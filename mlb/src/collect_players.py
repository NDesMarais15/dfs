from bs4 import BeautifulSoup
import urllib.request
import json
import re
import csv
import datetime
from src.teams import *

# date = datetime.date.today()
date = '2019-08-05'
fp = urllib.request.urlopen(
    "https://rotogrinders.com/projected-stats/mlb?site=draftkings&date=" + date)
my_bytes = fp.read()

my_str = my_bytes.decode("utf8")
fp.close()

soup = BeautifulSoup(my_str, 'html.parser')
decoder = json.JSONDecoder()
for script in soup.find_all('script'):
    if script.string is None:
        continue
    result = re.search('data =(.*)', script.string)
    if result is not None:
        # 6 is for data =
        # -1 is for the semicolon at the end of the expression
        hitters = json.loads(result.group(0)[6:-1])
        with open("%s hitters.csv" % date, "w+", newline='') as hitters_csv:
            csv_writer = csv.writer(hitters_csv, delimiter=',', quotechar='"')

            # Write column headers
            csv_writer.writerow(['Player_Name', 'Salary', 'Team', 'Pos', 'Opp', 'Proj_FP', 'Proj_Val',
                                 'Batting_Order_Confirmed_', 'Confirmed?'])

            for hitter in hitters:
                if hitter['team'] in teams:
                    try:
                        if 'confirmed' not in hitter.keys():
                            csv_writer.writerow([
                                hitter['player_name'],
                                hitter['salary'],
                                hitter['team'],
                                hitter['position'],
                                hitter['opp'],
                                hitter['points'],
                                hitter['pt/$/k']])
                        elif hitter['confirmed'] == 0:
                            print("%s's batting order is not confirmed" % hitter['player_name'])
                        csv_writer.writerow([
                            hitter['player_name'],
                            hitter['salary'],
                            hitter['team'],
                            hitter['position'],
                            hitter['opp'],
                            hitter['points'],
                            hitter['pt/$/k'],
                            hitter['order'],
                            hitter['confirmed']])
                    except KeyError:
                        print('Could not get info for %s' % hitter['player_name'])
