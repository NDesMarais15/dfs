import urllib.request
import json
import csv
from common import rg_teams


def collect_players(league, path, date, slate):
    # Date should be in the format month/day. Year is implied as far as I can tell
    if league == 'CFB':
        url = 'https://www.rotowire.com/daily/tables/optimizer-cfb.php' + \
              '?sport=CFB&site=DraftKings&projections=&type=main&slate=' + slate
    elif league == 'NHL':
        url = 'https://www.rotowire.com/daily/tables/optimizer-nhl.php' + \
              '?sport=NHL&site=DraftKings&projections=&type=main&slate=' + slate
    else:
        raise 'Unexpected value for league: %s' % league

    fp = urllib.request.urlopen(url)
    my_bytes = fp.read()

    my_str = my_bytes.decode('utf8')
    fp.close()

    decoded_json = json.loads(my_str)
    with open(path + '%s projections.csv' % date, 'w+', newline='') as players_csv:
        csv_writer = csv.writer(players_csv)
        csv_writer.writerow(['Name', 'Salary', 'Team', 'Pos', 'Opp', 'Proj_FP', 'Line', 'PP_Line'])
        for player in decoded_json:
            proj_points = player['proj_points'] if float(player['proj_points']) != 0.0 else 0.0
            if player['actual_position'] == 'D':
                line = 'x'
            else:
                line = player['even_strength_line']
            csv_writer.writerow([player['first_name'] + ' ' + player['last_name'],
                                 player['salary'],
                                 player['team'],
                                 player['actual_position'],
                                 player['opponent'].replace('@', ''),
                                 proj_points,
                                 line,
                                 player['power_play_line']])
