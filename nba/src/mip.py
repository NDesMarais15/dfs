import cvxpy
import numpy as np
from csv import writer
import pandas as pd
from player import Player
import math
import statistics
import collections


def generate_classic_lineups(date, projections_path, lineup_path, num_lineups, num_candidates,
                             lineup_overlap):
    with open(projections_path + '%s projections.csv' % date, 'r') as players_csv:
        players = pd.read_csv(players_csv)

    num_players = len(players['Salary'])
    teams = players['Team'].unique()
    num_teams = len(teams)

    # Create data structure for minimizing the number of players from the same team
    team_matrix = np.zeros((len(teams), num_players))
    for j in range(0, num_teams):
        for k in range(0, num_players):
            if players.iloc[k]['Team'] == teams[j]:
                team_matrix[j][k] = 1

    with open(lineup_path + '%s lineups overlap %s.csv' % (date, lineup_overlap), 'w+', newline='') as lineups_csv:
        # Initialize CSV writer and write first row. This will contain the final lineups in DK format
        csv_writer = writer(lineups_csv)
        csv_writer.writerow(['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL'])

        # Create rows for players to easily map their position
        # UTIL not included because that can be used for any player
        players['PG'] = 0
        players.loc[players['Pos'].str.contains('PG'), 'PG'] = 1

        players['SG'] = 0
        players.loc[players['Pos'].str.contains('SG'), 'SG'] = 1

        players['G'] = 0
        players.loc[players['Pos'].str.contains('PG') | players['Pos'].str.contains('SG'), 'G'] = 1

        players['SF'] = 0
        players.loc[players['Pos'].str.contains('SF'), 'SF'] = 1

        players['PF'] = 0
        players.loc[players['Pos'].str.contains('PF'), 'PF'] = 1

        players['F'] = 0
        players.loc[players['Pos'].str.contains('SF') | players['Pos'].str.contains('PF'), 'F'] = 1

        players['C'] = 0
        players.loc[players['Pos'].str.contains('C'), 'C'] = 1

        players['PG/SG'] = 0
        players.loc[(players['PG'] == 1) | (players['SG'] == 1), 'PG/SG'] = 1

        players['PG/SF'] = 0
        players.loc[(players['PG'] == 1) | (players['SF'] == 1), 'PG/SF'] = 1

        players['PG/PF'] = 0
        players.loc[(players['PG'] == 1) | (players['PF'] == 1), 'PG/PF'] = 1

        players['PG/C'] = 0
        players.loc[(players['PG'] == 1) | (players['C'] == 1), 'PG/C'] = 1

        players['SG/SF'] = 0
        players.loc[(players['SG'] == 1) | (players['SF'] == 1), 'SG/SF'] = 1

        players['SG/PF'] = 0
        players.loc[(players['SG'] == 1) | (players['PF'] == 1), 'SG/PF'] = 1

        players['SG/C'] = 0
        players.loc[(players['SG'] == 1) | (players['C'] == 1), 'SG/C'] = 1

        players['SF/PF'] = 0
        players.loc[(players['SF'] == 1) | (players['PF'] == 1), 'SF/PF'] = 1

        players['SF/C'] = 0
        players.loc[(players['SF'] == 1) | (players['C'] == 1), 'SF/C'] = 1

        players['PF/C'] = 0
        players.loc[(players['PF'] == 1) | (players['C'] == 1), 'PF/C'] = 1

        players['G/SF'] = 0
        players.loc[(players['G'] == 1) | (players['SF'] == 1), 'G/SF'] = 1

        players['G/PF'] = 0
        players.loc[(players['G'] == 1) | (players['PF'] == 1), 'G/PF'] = 1

        players['G/C'] = 0
        players.loc[(players['G'] == 1) | (players['C'] == 1), 'G/C'] = 1

        players['PG/F'] = 0
        players.loc[(players['PG'] == 1) | (players['F'] == 1), 'PG/F'] = 1

        players['SG/F'] = 0
        players.loc[(players['SG'] == 1) | (players['F'] == 1), 'SG/F'] = 1

        players['G/F'] = 0
        players.loc[(players['G'] == 1) | (players['F'] == 1), 'G/F'] = 1

        players['F/C'] = 0
        players.loc[(players['F'] == 1) | (players['C'] == 1), 'F/C'] = 1

        players['G/C'] = 0
        players.loc[(players['G'] == 1) | (players['C'] == 1), 'G/C'] = 1

        # We need a list to keep track of past lineups in order to enforce creation of unique lineups
        past_lineup_constraints = []

        # This is just a list of all ones in order to ensure that the number of players is 8
        ones = [1] * num_players

        # Variable for which players we ultimately select in a given lineup
        selection = cvxpy.Variable(num_players, boolean=True)

        # Total salary must not exceed $50,000
        salary_constraint = players['Salary'].to_numpy() @ selection <= 50000

        # At least 1 PG
        pg_constraint = players['PG'].to_numpy() @ selection >= 1

        # At least 1 SG
        sg_constraint = players['SG'].to_numpy() @ selection >= 1

        # At least 3 Gs (one PG, one SG, and one G)
        g_constraint = players['G'].to_numpy() @ selection >= 3

        # At least 1 SF
        sf_constraint = players['SF'].to_numpy() @ selection >= 1

        # At least 1 PF
        pf_constraint = players['PF'].to_numpy() @ selection >= 1

        # At least 3 Fs (one SF, one PF, and one F)
        f_constraint = players['F'].to_numpy() @ selection >= 3

        # At least 1 C
        c_constraint = players['C'].to_numpy() @ selection >= 1

        # These constraints ensure that we are not assuming we will be able to play the same
        # player in two different positions
        pgsf_constraint = players['PG/SF'].to_numpy() @ selection >= 2
        pgpf_constraint = players['PG/PF'].to_numpy() @ selection >= 2
        pgc_constraint = players['PG/C'].to_numpy() @ selection >= 2
        sgsf_constraint = players['SG/SF'].to_numpy() @ selection >= 2
        sgpf_constraint = players['SG/PF'].to_numpy() @ selection >= 2
        sgc_constraint = players['SG/C'].to_numpy() @ selection >= 2
        sfc_constraint = players['SF/C'].to_numpy() @ selection >= 2
        pfc_constraint = players['PF/C'].to_numpy() @ selection >= 2
        gf_constraint = players['G/F'].to_numpy() @ selection >= 6
        fc_constraint = players['F/C'].to_numpy() @ selection >= 4
        gc_constraint = players['G/C'].to_numpy() @ selection >= 4
        gsf_constraint = players['G/SF'].to_numpy() @ selection >= 4
        gpf_constraint = players['G/PF'].to_numpy() @ selection >= 4
        pgf_constraint = players['PG/F'].to_numpy() @ selection >= 4
        sgf_constraint = players['SG/F'].to_numpy() @ selection >= 4

        # Must have exactly 8 players in a lineup. This is a DK constraint
        players_constraint = ones @ selection == 8

        # Total number of projected fantasy points. This is what we are maximizing
        total_pts = players['Proj_FP'].to_numpy() @ selection

        # We add anti-stacking constraints to a list because they are on a per team basis,
        # so there are a variable amount depending on how many teams are in the slate
        team_constraints = []
        max_players_from_team = math.ceil(8 / num_teams)
        for team_index in range(0, num_teams):
            team_constraints.append(team_matrix[team_index] @ selection <= max_players_from_team)

        ownership_dict = {}
        rows = []
        # Generate lineups
        for candidate_count in range(0, num_candidates):
            # Add rule constraints
            constraints = [salary_constraint, pg_constraint, sg_constraint, g_constraint,
                           sf_constraint, pf_constraint, f_constraint, c_constraint,
                           pgsf_constraint, pgpf_constraint, pgc_constraint, sgsf_constraint,
                           sgpf_constraint, sgc_constraint, sfc_constraint,
                           pfc_constraint, gf_constraint, fc_constraint, gc_constraint,
                           gsf_constraint, gpf_constraint, pgf_constraint, sgf_constraint,
                           players_constraint]

            # Add team constraints
            constraints.extend(team_constraints)

            # Add past lineup constraints
            constraints.extend(past_lineup_constraints)

            # Formulate problem and solve
            problem = cvxpy.Problem(cvxpy.Maximize(total_pts), constraints)
            problem.solve(solver=cvxpy.GLPK_MI)
            if problem.solution.status == 'infeasible':
                print('Problem formulation is infeasible.')
                return
            solution_array = problem.solution.primal_vars[selection.id]

            # The solution array is a matrix of players in the order we collected them from
            # rotogrinders, so we have to do some work to actually write the lineups in a
            # way that will be readable by humans and eventually DraftKings
            row = [''] * 8

            player_obj_list = []
            ownership_list = []
            for i in range(0, len(solution_array)):
                if solution_array[i] == 1:
                    if candidate_count == 28:
                        print('hello')
                    player = Player(players.iloc[i]['Player_Name'])
                    if 'PG' in players.iloc[i]['Pos']:
                        player.legal_positions.append(0)

                    if 'SG' in players.iloc[i]['Pos']:
                        player.legal_positions.append(1)

                    if 'SF' in players.iloc[i]['Pos']:
                        player.legal_positions.append(2)

                    if 'PF' in players.iloc[i]['Pos']:
                        player.legal_positions.append(3)

                    if 'C' in players.iloc[i]['Pos']:
                        player.legal_positions.append(4)

                    if 'G' in players.iloc[i]['Pos']:
                        player.legal_positions.append(5)

                    if 'F' in players.iloc[i]['Pos']:
                        player.legal_positions.append(6)

                    player.legal_positions.append(7)
                    player_obj_list.append(player)
                    ownership_list.append(players.iloc[i]['pown%'])

            ownership_stdev = statistics.stdev(ownership_list)
            player_obj_list.sort(key=lambda p: len(p.legal_positions))
            for player_obj in player_obj_list:
                for legal_position in player_obj.legal_positions:
                    if row[legal_position] == '':
                        row[legal_position] = player_obj.name
                        break

            if '' in row:
                raise Exception('One of the lineup positions was not filled.')

            ownership_dict[candidate_count] = ownership_stdev
            rows.append(row)

            # Add lineup to past selections in order to create unique lineups
            past_lineup_constraints.append(solution_array @ selection <= lineup_overlap)

        ordered_ownership_dict = collections.OrderedDict(sorted(ownership_dict.items()))

        for lineup_count in range(0, num_lineups):
            csv_writer.writerow(rows[ordered_ownership_dict[0]])
