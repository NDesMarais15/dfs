import pandas as pd
import csv
import numpy as np

from common import rotogrinders
from nfl.src import mip

league = 'nfl'
strategy = '2R+1OppR+NoQBvsDef+NoRB&RB'
entry_dates = ['2020-11-13', '2020-11-19']
dates = ['2020-11-15', '2020-11-19']
weeks = [10, 11]
contest_ids = {'2020-11-13': '96410219', '2020-11-19': '96813915'}
num_lineups = 20


def calculate_places(lineup_file_name, standings_file_name):
    places = []
    points_list = []
    with open('../helper/Player Translations.csv') as translations_file:
        translations = pd.read_csv(translations_file, quotechar='"')
        with open(lineup_file_name) as lineup_file:
            with open(standings_file_name) as standings_file:
                standings = pd.read_csv(standings_file, quotechar='"')
                opp_points = np.flip(standings['Points'].to_numpy())
                lineup_reader = csv.reader(lineup_file)
                for row in lineup_reader:
                    points = 0
                    for value in row:
                        if value == 'QB':
                            break
                        player_points_array = standings.loc[standings['Player'] == value]['FPTS'].values
                        if len(player_points_array) == 0:
                            player_translation_array = translations.loc[translations['RG'] == value]['DK'].values
                            if len(player_translation_array) == 0:
                                print("Couldn't find point value for " + value)
                                continue
                            else:
                                value = player_translation_array[0]
                                player_points_array = standings.loc[standings['Player'] == value]['FPTS'].values
                                if len(player_points_array) == 0:
                                    print("Couldn't find point value for " + value)
                                    continue
                        points += player_points_array[0]
                    if points != 0:
                        points_list.append(round(points, 2))
                        # Zero-indexed, so add 1
                        places.append((len(opp_points) - opp_points.searchsorted(points)) + 1)
    print(points_list)
    print(places)
    return places


def calculate_payout(places):
    payoff = 0
    payout_df = pd.read_csv('../results/Week %d/%s/Payout.csv' % (week, entry_date))
    for place in places:
        index = payout_df['Minimum Place'].to_numpy().searchsorted(place, 'right')
        payoff += payout_df.iloc[index - 1]['Payout']
    return round(payoff, 2)


def generate_backtest_data(backtest_date, backtest_strategy, slate_id):
    for lineup_overlap_value in range(2, 8):
        rotogrinders.collect_players(league, backtest_date, '', slate_id)
        mip.generate_classic_lineups(backtest_date, '', '../strategies/%s/%s/' % (backtest_strategy,
                                                                                  backtest_date),
                                     num_lineups, lineup_overlap_value, backtest_strategy)


def write_teams(date_to_write, week_to_write):
    with open('../../common/teams.py', 'w+') as teams:
        with open('../results/Week %d/%s/teams.py' % (week_to_write, date_to_write)) as old_teams:
            teams.write(old_teams.read())


for i in range(0, 2):
    entry_date = entry_dates[i]
    date = dates[i]
    week = weeks[i]
    write_teams(entry_date, week)
    generate_backtest_data(date, strategy, -1)
    with open('../strategies/%s/%s/Payouts.csv' % (strategy, date), 'w+', newline='') as payouts_file:
        csv_writer = csv.writer(payouts_file)
        csv_writer.writerow(['Overlap', 'Payout'])
        for j in range(2, 8):
            payout = calculate_payout(
                calculate_places('../strategies/%s/%s/%s lineups overlap %d.csv'
                                 % (strategy, date, date, j),
                                 '../results/Week %d/%s/contest-standings-%s.csv' % (week, entry_date,
                                                                                     contest_ids[entry_date])))
            csv_writer.writerow([j, payout])
