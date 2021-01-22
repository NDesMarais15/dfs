import pandas as pd
import csv
import numpy as np

from common import rotogrinders
from nfl.src import mip

league = 'nfl'
strategy = '2R+1OppR+NoPlayervsDef+NoRB&RB'
entry_dates = ['2020-11-13', '2020-11-19', '2021-01-09', '2021-01-10']
dates = ['2020-11-15', '2020-11-19', '2021-01-09', '2021-01-10']
slates = [1, 1, 2, 3]
weeks = [10, 11, 18, 18]
contest_ids = {'2020-11-13': '96410219', '2020-11-19': '96813915',
               '2021-01-09': '100391197', '2021-01-10': '100509179'}
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


def calculate_payout(payout_places, payout_week, payout_slate):
    payoff = 0
    payout_df = pd.read_csv('../results/Week %d/Classic/Slate %d/Payout.csv' % (payout_week, payout_slate))
    for place in payout_places:
        index = payout_df['Minimum Place'].to_numpy().searchsorted(place, 'right')
        payoff += payout_df.iloc[index - 1]['Payout']
    return round(payoff, 2)


def generate_backtest_data(backtest_date, backtest_week, backtest_slate, backtest_strategy, slate_id):
    for lineup_overlap_value in range(2, 8):
        rotogrinders.collect_players(league, backtest_date, '', slate_id)
        backtest_path = '../strategies/%s/Week %d/Classic/Slate %d/' \
                        % (backtest_strategy, backtest_week, backtest_slate)
        mip.generate_classic_lineups(backtest_date, '', backtest_path,
                                     num_lineups, lineup_overlap_value, backtest_strategy)


def write_teams(week_to_write, slate_to_write):
    with open('../../common/teams.py', 'w+') as teams:
        with open('../results/Week %d/Classic/Slate %d/teams.py' % (week_to_write, slate_to_write)) as old_teams:
            teams.write(old_teams.read())


for i in range(0, 4):
    entry_date = entry_dates[i]
    date = dates[i]
    week = weeks[i]
    slate = slates[i]
    write_teams(week, slate)
    generate_backtest_data(date, week, slate, strategy, -1)
    payouts_path = '../strategies/%s/Week %d/Classic/Slate %d/Payouts.csv' % (strategy, week, slate)
    with open(payouts_path, 'w+', newline='') as payouts_file:
        csv_writer = csv.writer(payouts_file)
        csv_writer.writerow(['Overlap', 'Payout'])
        for j in range(2, 8):
            lineup_path = '../strategies/%s/Week %d/Classic/Slate %d/%s lineups overlap %d.csv' \
                          % (strategy, week, slate, date, j)
            results_path = '../results/Week %d/Classic/Slate %d/contest-standings-%s.csv' \
                           % (week, slate, contest_ids[entry_date])
            calculated_places = calculate_places(lineup_path, results_path)
            payout = calculate_payout(calculated_places, week, slate)
            csv_writer.writerow([j, payout])
