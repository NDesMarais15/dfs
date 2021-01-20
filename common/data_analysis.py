import os
import csv
import pandas as pd
import matplotlib.pyplot as plt

termination_string = 'file transmission terminated after approx. 20 lines.'

def write_aggregate_stats_nfl():
    with open('../nfl/helper/Aggregate Stats.csv', 'w+', newline='') as aggregate_stats:
        csv_writer = csv.writer(aggregate_stats, delimiter=',', quotechar='"')
        csv_writer.writerow(['Date', 'Player Name', 'Position', 'Team', 'Opponent',
                             'Home/Away', 'Salary', 'Projected', 'Actual'])

        for file_name in os.listdir('../nfl/historical'):
            if not file_name.endswith('csv'):
                continue
            with open('../nfl/historical/' + file_name) as file:
                if 'actual' in file_name:
                    player_dict = {}
                    rotoguru_players = pd.read_csv(file, sep=';')
                    for index, rotoguru_player in rotoguru_players.iterrows():
                        split_name = rotoguru_player['Name'].split(',')
                        if len(split_name) == 1:
                            name = split_name[0]
                        else:
                            name = split_name[1].strip() + ' ' + split_name[0]
                        player_dict[name] = [''] * 9
                        player_dict[name][0] = file_name.split()[0]
                        player_dict[name][1] = name
                        player_dict[name][2] = rotoguru_player['Pos']
                        player_dict[name][3] = rotoguru_player['Team']
                        player_dict[name][4] = rotoguru_player['Oppt']
                        player_dict[name][5] = rotoguru_player['h/a']
                        player_dict[name][6] = rotoguru_player['DK salary']
                        player_dict[name][8] = rotoguru_player['DK points']

                elif 'projections' in file_name:
                    rotogrinders_players = pd.read_csv(file)
                    for index, rotogrinders_player in rotogrinders_players.iterrows():
                        if not rotogrinders_player['Player_Name'] in player_dict:
                            print('Could not add ' + rotogrinders_player['Player_Name'] + ' to data sheet.')
                            continue
                        player_dict[rotogrinders_player['Player_Name']][7] = rotogrinders_player['Proj_FP']
                        csv_writer.writerow(player_dict[rotogrinders_player['Player_Name']])


def scatter():
    sundays = pd.read_csv('../nfl/helper/Sundays.csv')
    aggregate_stats = pd.read_csv('../nfl/helper/Aggregate Stats.csv')
    for year in range(2016, 2021):
        for date in sundays[str(year)]:
            filtered_stats = aggregate_stats.loc[aggregate_stats['Date'] == date]
            plt.scatter(filtered_stats['Projected'], filtered_stats['Actual'])
            plt.title(date)
            plt.show()


def cleanup_historical_projections_nba():
    for file_name in os.listdir('../nba/historical'):
        if not file_name.endswith('.csv'):
            continue
        full_path = '../nba/historical/' + file_name
        with open(full_path) as file:
            projections = pd.read_csv(file)
            if projections.size == 0:
                delete_file = True
            else:
                delete_file = False

        if delete_file:
            os.remove(full_path)


def write_aggregate_stats_nba():
    with open('../nba/helper/Aggregate Stats.csv', 'w+', newline='') as aggregate_stats:
        csv_writer = csv.writer(aggregate_stats, delimiter=',')
        csv_writer.writerow(['Date', 'Player Name', 'Position', 'Team', 'Opponent',
                             'Home/Away', 'Salary', 'Projected', 'Actual'])

        for file_name in os.listdir('../nba/historical'):
            if not file_name.endswith('csv'):
                continue
            with open('../nba/historical/' + file_name) as file:
                if 'actual' in file_name:
                    player_dict = {}
                    rotoguru_players = pd.read_csv(file, sep=';')
                    for index, rotoguru_player in rotoguru_players.iterrows():
                        # Rotoguru limits some of their files to only 20 lines if you don't pay
                        # For what I'm doing, the full dataset isn't really necessary
                        if rotoguru_player['Date'] == termination_string:
                            break
                        split_name = rotoguru_player['Name'].split(',')
                        if len(split_name) == 1:
                            name = split_name[0]
                        else:
                            name = split_name[1].strip() + ' ' + split_name[0]

                        # Rotoguru is missing some data for position and salary. We just want to skip
                        # this player
                        if pd.isna(rotoguru_player['DK Salary']) or pd.isna(rotoguru_player['Pos']):
                            continue

                        player_dict[name] = [''] * 9
                        player_dict[name][0] = file_name.split()[0]
                        player_dict[name][1] = name
                        player_dict[name][2] = rotoguru_player['Pos']
                        player_dict[name][3] = rotoguru_player['Team']
                        player_dict[name][4] = rotoguru_player['Oppt']
                        player_dict[name][5] = rotoguru_player['H/A']
                        player_dict[name][6] = rotoguru_player['DK Salary']
                        player_dict[name][8] = rotoguru_player['DK Pts']

                elif 'projections' in file_name:
                    rotogrinders_players = pd.read_csv(file)
                    for index, rotogrinders_player in rotogrinders_players.iterrows():
                        if not rotogrinders_player['Player_Name'] in player_dict:
                            print('Could not add ' + rotogrinders_player['Player_Name'] + ' to data sheet.')
                            continue
                        player_dict[rotogrinders_player['Player_Name']][7] = rotogrinders_player['Proj_FP']
                        csv_writer.writerow(player_dict[rotogrinders_player['Player_Name']])


write_aggregate_stats_nba()
