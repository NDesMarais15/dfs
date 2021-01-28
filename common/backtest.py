import pandas as pd
import csv
import numpy as np


def calculate_places(league, lineup_file_name, standings_file_name):
    if league == 'nfl':
        header_indicator = 'QB'
    elif league == 'nba':
        header_indicator = 'PG'
    else:
        raise Exception('Unexpected league value: %s' % league)

    places = []
    points_list = []
    with open('../../%s/helper/Player Translations.csv' % league) as translations_file:
        translations = pd.read_csv(translations_file, quotechar='"')
        with open(lineup_file_name) as lineup_file:
            with open(standings_file_name) as standings_file:
                standings = pd.read_csv(standings_file, quotechar='"')
                opp_points = np.flip(standings['Points'].to_numpy())
                lineup_reader = csv.reader(lineup_file)
                for row in lineup_reader:
                    points = 0
                    for value in row:
                        if value == header_indicator:
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
