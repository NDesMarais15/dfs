import urllib.request
import json
import csv
import datetime
from src.teams import *


def collect_players(path, date, slate):
    # Date should be in the format month/day. Year is implied as far as I can tell
    url = 'https://www.rotowire.com/daily/tables/optimizer-cfb.php' + \
          '?sport=CFB&site=DraftKings&projections=&type=main&slate=' + slate + '%20-%20' + date
    print(url)
    fp = urllib.request.urlopen(url)
    my_bytes = fp.read()

    my_str = my_bytes.decode('utf8')
    fp.close()

    decoded_json = json.loads(my_str)

    # Rotowire expects 12/3, mip.py expects 12/03
    date_day = date.split('/')[1]
    if len(date_day) == 1:
        date = date.replace(date_day, '0' + date_day)

    file_friendly_date = str(datetime.date.today().year) + '-' + date.replace('/', '-')
    with open(path + '%s projections.csv' % file_friendly_date, 'w+', newline='') as players_csv:
        csv_writer = csv.writer(players_csv)
        csv_writer.writerow(['Name', 'Salary', 'Team', 'Pos', 'Opp', 'Proj_FP'])
        for player in decoded_json:
            proj_points = player['proj_points'] if float(player['proj_points']) != 0.0 else 0.0
            if player['team'] in teams:
                csv_writer.writerow([player['first_name'] + ' ' + player['last_name'],
                                     player['salary'],
                                     player['team'],
                                     player['actual_position'],
                                     player['opponent'].replace('@', ''),
                                     proj_points])
