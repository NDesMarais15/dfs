import cvxpy
import numpy as np
from csv import writer
import pandas as pd
from player import Player


def generate_classic_lineups(date, projections_path, lineup_path, num_lineups, lineup_overlap):
    with open(projections_path + '%s projections.csv' % date, 'r') as players_csv:
        players = pd.read_csv(players_csv)

    num_players = len(players['Salary'])

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

        players['G/F'] = 0
        players.loc[(players['G'] == 1) | (players['F'] == 1), 'G/F'] = 1

        players['F/C'] = 0
        players.loc[(players['F'] == 1) | (players['C'] == 1), 'F/C'] = 1

        players['G/C'] = 0
        players.loc[(players['G'] == 1) | (players['C'] == 1), 'G/C'] = 1

        # We need a list to keep track of past lineups in order to enforce creation of unique lineups
        past_selections = [0] * num_players

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
        gf_constraint = players['G/F'].to_numpy() @ selection >= 6
        fc_constraint = players['F/C'].to_numpy() @ selection >= 4
        gc_constraint = players['G/C'].to_numpy() @ selection >= 4

        # Must have exactly 8 players in a lineup. This is a DK constraint
        players_constraint = ones @ selection == 8

        # Total number of projected fantasy points. This is what we are maximizing
        total_pts = players['Proj_FP'].to_numpy() @ selection

        # Generate lineups
        for lineup_count in range(0, num_lineups):
            # Constraint to limit overlap with previously generated lineups
            past_lineups_constraint = past_selections @ selection <= lineup_overlap

            # Add rule constraints
            constraints = [salary_constraint, pg_constraint, sg_constraint, g_constraint,
                           sf_constraint, pf_constraint, f_constraint, c_constraint, gf_constraint,
                           fc_constraint, gc_constraint, players_constraint, past_lineups_constraint]

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
            for i in range(0, len(solution_array)):
                if solution_array[i] == 1:
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

            player_obj_list.sort(key=lambda p: len(p.legal_positions))
            for player_obj in player_obj_list:
                for legal_position in player_obj.legal_positions:
                    if row[legal_position] == '':
                        row[legal_position] = player_obj.name
                        break

            if '' in row:
                raise Exception('One of the lineup positions was not filled.')

            csv_writer.writerow(row)

            # Add lineup to past selections in order to create unique lineups
            past_selections = np.logical_or(solution_array, past_selections)
