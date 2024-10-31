import cvxpy
import numpy as np
from csv import writer
import pandas as pd


def generate_classic_lineups(date, projections_path, lineup_path, num_lineups, lineup_overlap, strategy):
    with open(projections_path + '%s projections.csv' % date, 'r') as players_csv:
        players = pd.read_csv(players_csv)

    teams = players['Team'].unique()
    num_players = len(players['Salary'])
    with open(lineup_path + '%s lineups overlap %s.csv' % (date, lineup_overlap), 'w+', newline='') as lineups_csv:
        # Initialize matrices (num_teams x num_players)
        center_team_matrix = np.zeros((len(teams), num_players))
        winger_team_matrix = np.zeros((len(teams), num_players))
        defenseman_team_matrix = np.zeros((len(teams), num_players))
        goalie_team_matrix = np.zeros((len(teams), num_players))
        goalie_opp_matrix = np.zeros((len(teams), num_players))
        opp_matrix = np.zeros((len(teams), num_players))

        # We need matrices of players that map team to position for the stacking constraints
        for j in range(0, len(teams)):
            for k in range(0, len(players)):
                if players.iloc[k]['Team'] == teams[j]:
                    if players.iloc[k]['Pos'] == 'C':
                        center_team_matrix[j][k] = 1

                    elif players.iloc[k]['Pos'] == 'W':
                        winger_team_matrix[j][k] = 1

                    elif players.iloc[k]['Pos'] == 'D':
                        defenseman_team_matrix[j][k] = 1

                    elif players.iloc[k]['Pos'] == 'G':
                        goalie_team_matrix[j][k] = 1

                    else:
                        raise ValueError('Unexpected position: ' + players.iloc[k]['Pos'])

                elif players.iloc[k]['Opp'] == teams[j]:
                    opp_matrix[j][k] = 1

                    if players.iloc[k]['Pos'] == 'G':
                        goalie_opp_matrix[j][k] = 1

        # Initialize CSV writer and write first row. This will contain the final lineups in DK format
        csv_writer = writer(lineups_csv)
        csv_writer.writerow(['C', 'C', 'C', 'W', 'W', 'W', 'D', 'D', 'G', 'UTIL'])

        # Create rows for players to easily map their position
        # UTIL not included since that can be used for C, W, or D
        players['Skater'] = 0
        players.loc[(players['Pos'] == 'C') | (players['Pos'] == 'W') | (players['Pos'] == 'D'), 'Skater'] = 1

        players['C'] = 0
        players.loc[players['Pos'] == 'C', 'C'] = 1

        players['W'] = 0
        players.loc[players['Pos'] == 'W', 'W'] = 1

        players['D'] = 0
        players.loc[players['Pos'] == 'D', 'D'] = 1

        players['G'] = 0
        players.loc[players['Pos'] == 'G', 'G'] = 1

        # We need a list to keep track of past lineups in order to enforce creation of unique lineups
        past_lineup_constraints = []

        # This is just a list of all ones in order to ensure that the number of players is 9
        ones = [1] * num_players

        # Variable for which players we ultimately select in a given lineup
        selection = cvxpy.Variable(num_players, boolean=True)

        # Total salary must not exceed $50,000
        salary_constraint = players['Salary'].to_numpy() @ selection <= 50_000

        # Exactly 8 skaters
        skater_constraint = players['Skater'].to_numpy() @ selection == 8

        # At least 2 Cs, but not more than 3 (to account for UTIL)
        center_constraint_1 = players['C'].to_numpy() @ selection >= 2
        center_constraint_2 = players['C'].to_numpy() @ selection <= 3

        # At least 3 Ws, but no more than 4 (to account for UTIL)
        winger_constraint_1 = players['W'].to_numpy() @ selection >= 3
        winger_constraint_2 = players['W'].to_numpy() @ selection <= 4

        # At least 2 Ds, but no more than 3 (to account for UTIL)
        defenseman_constraint_1 = players['D'].to_numpy() @ selection >= 2
        defenseman_constraint_2 = players['D'].to_numpy() @ selection <= 3

        # At least 1 G, but no more than 2 (to account for FLEX)
        goalie_constraint_1 = players['G'].to_numpy() @ selection >= 1
        goalie_constraint_2 = players['G'].to_numpy() @ selection <= 2

        # Must have exactly 9 players in a lineup. This is a DK constraint
        players_constraint = ones @ selection == 9

        # We add stacking constraints to a list because they are on a per-team basis,
        # so there are a variable amount depending on how many teams are in the slate
        team_stack_constraints = []
        for i in range(0, len(center_team_matrix)):
            # No player can play against his own defense. Any offensive player's points are
            # going to be negatively correlated, but this might be a little too restrictive.
            # More testing is necessary to reach a verdict. Uses Big M constraint
            if 'NoSkatervsG' in strategy:
                team_stack_constraints.append(((goalie_team_matrix[i] @ selection) * 1000) + (opp_matrix[i] @ selection)
                                              <= 1000)

        # Total number of projected fantasy points. This is what we are maximizing
        total_pts = players['Proj_FP'].to_numpy() @ selection

        # Generate lineups
        for lineup_count in range(0, num_lineups):
            # Add rule constraints
            constraints = [salary_constraint, skater_constraint, center_constraint_1, center_constraint_2,
                           winger_constraint_1, winger_constraint_2, defenseman_constraint_1, defenseman_constraint_2,
                           goalie_constraint_1, goalie_constraint_2, players_constraint]

            # Add stacking constraints
            constraints.extend(team_stack_constraints)

            # Add past lineup constraints
            constraints.extend(past_lineup_constraints)

            # Formulate problem and solve
            problem = cvxpy.Problem(cvxpy.Maximize(total_pts), constraints)

            problem.solve(solver=cvxpy.GLPK_MI)
            if problem.solution.status == 'infeasible':
                print('Problem formulation is infeasible.')
                return
            solution_array = problem.solution.primal_vars[selection.id]

            # The solution array is a matrix of players in the order we collected them,
            # so we have to do some work to actually write the lineups in a
            # way that will be readable by humans and eventually DraftKings
            center_index = 0
            winger_index = 2
            defenseman_index = 5
            goalie_index = 7
            util_index = 8
            row = [''] * 9
            for i in range(0, len(solution_array)):
                if solution_array[i] == 1:
                    player = players.iloc[i]
                    if player['Pos'] == 'C':
                        if center_index == 2:
                            center_index = util_index
                        row[center_index] = player['Player_Name']
                        center_index += 1
                    elif player['Pos'] == 'W':
                        if winger_index == 5:
                            winger_index = util_index
                        row[winger_index] = player['Player_Name']
                        winger_index += 1
                    elif player['Pos'] == 'D':
                        if defenseman_index == 7:
                            defenseman_index = util_index
                        row[defenseman_index] = player['Player_Name']
                        defenseman_index += 1
                    elif player['Pos'] == 'G':
                        row[goalie_index] = player['Player_Name']
                        goalie_index += 1
            csv_writer.writerow(row)

            # Add lineup to past selections in order to create unique lineups
            past_lineup_constraints.append(solution_array @ selection <= lineup_overlap)
