from bs4 import BeautifulSoup
import urllib.request
import json
import re
import csv
from teams import *


# Slate ID of -1 means grab their default salary, which is for the main slate of the week
def collect_players(date, path, slate_id):
    fp = urllib.request.urlopen(
        'https://rotogrinders.com/projected-stats/nfl?site=draftkings&date=%s' % date)
    my_bytes = fp.read()

    my_str = my_bytes.decode('utf8')
    fp.close()

    soup = BeautifulSoup(my_str, 'html.parser')
    for script in soup.find_all('script'):
        if script.string is None:
            continue
        result = re.search('data =(.*)', script.string)
        if result is not None:
            # 6 is for data =
            # -1 is for the semicolon at the end of the expression
            players = json.loads(result.group(0)[6:-1])
            with open(path + '%s projections.csv' % date, 'w+', newline='') as players_csv:
                csv_writer = csv.writer(players_csv, delimiter=',', quotechar='"')

                # Write column headers
                csv_writer.writerow(['Player_Name', 'Salary', 'Team', 'Pos', 'Opp', 'Proj_FP'])

                for player in players:
                    if player['team'] in teams:
                        try:
                            salary = 0
                            fpts = 0
                            if slate_id == -1:
                                if player['salary'] == 'N/A':
                                    print('Could not find salary data for ' + player['player_name'])
                                    continue
                                else:
                                    salary = player['salary']
                                    fpts = player['points']
                            else:
                                if player['import_data'] is None:
                                    print('Could not find salary data for ' + player['player_name'])
                                    continue
                                for slate in player['import_data']:
                                    if slate['slate_id'] == slate_id:
                                        salary = slate['salary']
                                        fpts = slate['fpts']

                            csv_writer.writerow([
                                player['player_name'],
                                salary,
                                player['team'],
                                player['position'],
                                player['opp'],
                                fpts])
                        except KeyError:
                            print('Could not get info for %s' % player['player_name'])
