from urllib.error import HTTPError, URLError

from bs4 import BeautifulSoup
import urllib.request
import csv

def collect_players(league, date, path, slate=None):
    if slate is None:
        url = 'https://www.dailyfantasyfuel.com/%s/projections/draftkings/%s/' % (league, date)
    else:
        url = 'https://www.dailyfantasyfuel.com/%s/projections/draftkings/%s?slate=%s' % (league, date, slate)

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


        if league == 'nfl':
            header = ['Player_Name', 'Salary', 'Team', 'Pos', 'Opp', 'Proj_FP', 'pown%']
        elif league == 'nhl':
            header = ['Player_Name', 'Salary', 'Team', 'Pos', 'Opp', 'Proj_FP', 'Reg_Line', 'PP_Line']
        else:
            raise ValueError('Unexpected league: ' + league)

        # Write column header
        csv_writer.writerow(header)

        for tr in soup.find_all('tr', class_='projections-listing'):
            try:
                if league == 'nfl':
                    row = [tr['data-name'], tr['data-salary'], tr['data-team'], tr['data-pos'], tr['data-opp'],
                           tr['data-ppg_proj'], '']
                elif league == 'nhl':
                    row = [tr['data-name'], tr['data-salary'], tr['data-team'], tr['data-pos'], tr['data-opp'],
                           tr['data-ppg_proj'], tr['data-reg_line'], tr['data-pp_line']]
                else:
                    raise ValueError('Unexpected league: ' + league)

                csv_writer.writerow(row)
            except KeyError:
                print('Could not get info for %s' % tr['data-name'])
