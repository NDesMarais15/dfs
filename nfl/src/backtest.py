import pandas as pd
import csv
import numpy as np


strategy = '2R+1OppR+NoQBvsDef+NoRB&RB'
entry_date = '2020-11-19'
date = '2020-11-19'
week = 11
contest_ids = {'2020-11-13': '96410219', '2020-11-19': '96813915'}


def calculate_places(lineup_file_name, standings_file_name):
    places = []
    points_list = []
    with open('../Helper Data/Player Translations.csv') as translations_file:
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
    payout_df = pd.read_csv('../Results/Week %d/%s/Payout.csv' % (week, entry_date))
    for place in places:
        index = payout_df['Minimum Place'].to_numpy().searchsorted(place, 'right')
        payoff += payout_df.iloc[index - 1]['Payout']
    return round(payoff, 2)


with open('../Strategies/%s/%s/Payouts.csv' % (strategy, date), 'w+', newline='') as payouts_file:
    csv_writer = csv.writer(payouts_file)
    csv_writer.writerow(['Overlap', 'Payout'])
    for i in range(2, 8):
        payout = calculate_payout(
            calculate_places('../Strategies/%s/%s/%s lineups overlap %d.csv'
                             % (strategy, date, date, i),
                             '../Results/Week %d/%s/contest-standings-%s.csv' % (week, entry_date,
                                                                                 contest_ids[entry_date])))
        csv_writer.writerow([i, payout])
