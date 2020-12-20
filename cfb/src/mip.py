import cvxpy
import pandas as pd
import numpy as np
import csv


def generate_classic_lineups(date, path, num_lineups, lineup_overlap, strategy):
    with open(path + '%s projections.csv' % date, 'r') as players_csv:
        players = pd.read_csv(players_csv)

    teams = players['Team'].unique()
    with open(path + '%s lineups overlap %s.csv' % (date, lineup_overlap), 'w+', newline='') as lineups_csv:
        # Initialize matrices (num_teams x num_players)
        qb_team_matrix = np.zeros((len(teams), len(players['Salary'])))
        wr_team_matrix = np.zeros((len(teams), len(players['Salary'])))
        rb_team_matrix = np.zeros((len(teams), len(players['Salary'])))
        team_to_opp_indices = {}

        # We need matrices of players that map team to position for the stacking constraints
        for j in range(0, len(teams)):
            for k in range(0, len(players)):
                if players.iloc[k]['Team'] == teams[j]:
                    if players.iloc[k]['Pos'] == 'QB':
                        qb_team_matrix[j][k] = 1

                    elif players.iloc[k]['Pos'] == 'WR':
                        wr_team_matrix[j][k] = 1

                    elif players.iloc[k]['Pos'] == 'RB':
                        rb_team_matrix[j][k] = 1

                if players.iloc[k]['Opp'] == teams[j]:
                    # This creates a dict of team index -> opp index
                    # We use this to create a stacking constraint which forces opposing quarterbacks
                    team_index = np.where(teams == players.iloc[k]['Team'])[0][0]
                    opp_index = np.where(teams == players.iloc[k]['Opp'])[0][0]
                    team_to_opp_indices[team_index] = opp_index

        csv_writer = csv.writer(lineups_csv)
        csv_writer.writerow(['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'FLEX', 'S-FLEX'])

        # Create rows for players to easily map their position
        # FLEX not included since that can be used for RB or WR
        # S-FLEX not included since that can be used for RB, WR, or QB
        players['QB'] = 0
        players.loc[players['Pos'] == 'QB', 'QB'] = 1

        players['WR'] = 0
        players.loc[players['Pos'] == 'WR', 'WR'] = 1

        players['RB'] = 0
        players.loc[players['Pos'] == 'RB', 'RB'] = 1

        # We need a list to keep track of past lineups in order to enforce creation of unique lineups
        past_selections = [0] * len(players['Salary'])

        # This is just a list of all ones in order to ensure that the number of players is 8
        ones = [1] * len(players['Salary'])

        # Variable for which players we ultimately select in a given lineup
        selection = cvxpy.Variable(len(players['Salary']), boolean=True)

        # Total salary must not exceed $50,000
        salary_constraint = players['Salary'].to_numpy() @ selection <= 50_000

        # At least 1 QBs, but no more than 2 (to account for S-FLEX)
        qb_constraint_1 = players['QB'].to_numpy() @ selection >= 1
        qb_constraint_2 = players['QB'].to_numpy() @ selection <= 2

        # At least 2 RBs, but no more than 4 (to account for FLEX and S-FLEX)
        rb_constraint_1 = players['RB'].to_numpy() @ selection >= 2
        rb_constraint_2 = players['RB'].to_numpy() @ selection <= 4

        # At least 3 WRs, but no more than 4 (to account for FLEX and S-FLEX)
        wr_constraint_1 = players['WR'].to_numpy() @ selection >= 3
        wr_constraint_2 = players['WR'].to_numpy() @ selection <= 5

        # Must have exactly 8 players in a lineup. This is a DK constraint
        players_constraint = ones @ selection == 8

        # We add stacking constraints to a list because they are on a per team basis,
        # so there are a variable amount depending on how many teams are in the slate
        team_stack_constraints = []

        if '2QB' in strategy:
            # 2 QBs
            team_stack_constraints.append(players['QB'].to_numpy() @ selection == 2)

        for i in range(0, len(qb_team_matrix)):
            if '2WR' in strategy:
                # 2 WRs per QB
                team_stack_constraints.append((qb_team_matrix[i] @ selection) * 2
                                              <= wr_team_matrix[i] @ selection)

            if '1WR' in strategy:
                # 1 WR per QB
                team_stack_constraints.append(qb_team_matrix[i] @ selection
                                              <= wr_team_matrix[i] @ selection)

            if 'NoRB&RB' in strategy:
                # No two running backs from the same team. RBs compete for carries, so including two
                # from the same team limits upside.
                team_stack_constraints.append((rb_team_matrix[i] @ selection) <= 1)

            if 'QBvsQB' in strategy:
                # QB vs. opp QB
                team_stack_constraints.append(qb_team_matrix[i] @ selection
                                              == qb_team_matrix[team_to_opp_indices[i]] @ selection)

        # Total number of projected fantasy points. This is what we are maximizing
        total_pts = players['Proj_FP'].to_numpy() @ selection

        # Generate lineups
        for lineup_count in range(0, num_lineups):
            # Constraint to limit overlap with previously generated lineups
            past_lineups_constraint = past_selections @ selection <= lineup_overlap
            constraints = [salary_constraint, qb_constraint_1, qb_constraint_2, rb_constraint_1,
                           rb_constraint_2, wr_constraint_1, wr_constraint_2, players_constraint,
                           past_lineups_constraint]

            # Add stacking constraints
            constraints.extend(team_stack_constraints)

            # Formulate problem and solve
            problem = cvxpy.Problem(cvxpy.Maximize(total_pts), constraints)
            problem.solve(solver=cvxpy.GLPK_MI)
            if problem.solution.status == 'infeasible':
                print('Problem formulation is infeasible.')
                return
            solution_array = problem.solution.primal_vars[selection.id]

            # The solution array is a matrix of players in the order we collected them from
            # rotowire, so we have to do some work to actually write the lineups in a
            # way that will be readable by humans and eventually DraftKings
            qb_index = 0
            rb_index = 1
            wr_index = 3
            flex_index = 6
            s_flex_index = 7
            row = [''] * 8
            for i in range(0, len(solution_array)):
                if solution_array[i] == 1:
                    player = players.iloc[i]
                    if player['Pos'] == 'QB':
                        row[qb_index] = player['Name']
                        qb_index = s_flex_index
                    elif player['Pos'] == 'RB':
                        if rb_index == 3:
                            rb_index = flex_index
                        row[rb_index] = player['Name']
                        rb_index += 1
                    elif player['Pos'] == 'WR':
                        row[wr_index] = player['Name']
                        wr_index += 1
            csv_writer.writerow(row)

            # Add lineup to past selections in order to create unique lineups
            past_selections = np.logical_or(solution_array, past_selections)


def generate_showdown_lineups(date, path, num_lineups, lineup_overlap):
    with open(path + '%s projections.csv' % date, 'r') as players_csv:
        players = pd.read_csv(players_csv)

    teams = players['Team'].unique()
    num_players = len(players['Salary'])

    # Variable for which players we ultimately select in a given lineup
    selection = cvxpy.Variable(num_players * 2, boolean=True)

    captain_list = []
    captain_constraint_list = []
    for (index, player) in players.iterrows():
        player_dict = {'Name': player['Name'],
                       'Salary': player['Salary'] * 1.5,
                       'Team': player['Team'],
                       'Pos': player['Pos'],
                       'Opp': player['Opp'],
                       'Proj_FP': player['Proj_FP'] * 1.5}
        captain_list.append(player_dict)
        captain_constraint_list.append(selection[index] + selection[index + num_players] <= 1)

    players = pd.concat([players, pd.DataFrame(captain_list)])

    # This is just a list of all ones in order to ensure that the number of players is 6
    ones = [1] * (num_players * 2)

    # Must have exactly 6 players in a lineup. This is a DK constraint
    players_constraint = ones @ selection == 6

    half_ones = [1] * num_players
    half_zeros = np.zeros(num_players)
    flex_ones = np.concatenate([half_ones, half_zeros])
    captain_ones = np.concatenate([half_zeros, half_ones])

    # Total salary must not exceed $50,000
    salary_constraint = players['Salary'].to_numpy() @ selection <= 50_000

    flex_constraint = flex_ones @ selection == 5
    captain_constraint = captain_ones @ selection == 1

    # Initialize matrices (num_teams x num_players)
    qb_team_matrix = np.zeros((len(teams), len(players['Salary'])))
    wr_team_matrix = np.zeros((len(teams), len(players['Salary'])))
    rb_team_matrix = np.zeros((len(teams), len(players['Salary'])))
    team_to_opp_indices = {}

    # We need matrices of players that map team to position for the stacking constraints
    for j in range(0, len(teams)):
        for k in range(0, len(players)):
            if players.iloc[k]['Team'] == teams[j]:
                if players.iloc[k]['Pos'] == 'QB':
                    qb_team_matrix[j][k] = 1

                elif players.iloc[k]['Pos'] == 'WR':
                    wr_team_matrix[j][k] = 1

                elif players.iloc[k]['Pos'] == 'RB':
                    rb_team_matrix[j][k] = 1

            if players.iloc[k]['Opp'] == teams[j]:
                # This creates a dict of team index -> opp index
                # We use this to create a stacking constraint which forces opposing quarterbacks
                if players.iloc[k]['Pos'] == 'QB':
                    team_index = np.where(teams == players.iloc[k]['Team'])[0][0]
                    opp_index = np.where(teams == players.iloc[k]['Opp'])[0][0]
                    team_to_opp_indices[team_index] = opp_index

    # We add stacking constraints to a list because they are on a per team basis,
    # so there are a variable amount depending on how many teams are in the slate
    team_stack_constraints = []
    for i in range(0, len(qb_team_matrix)):
        # 2 WRs per QB
        team_stack_constraints.append((qb_team_matrix[i] @ selection) * 2
                                      <= wr_team_matrix[i] @ selection)

        # No two running backs from the same team. RBs compete for carries, so including two
        # from the same team limits upside.
        team_stack_constraints.append((rb_team_matrix[i] @ selection) <= 1)

    # Total number of projected fantasy points. This is what we are maximizing
    total_pts = players['Proj_FP'].to_numpy() @ selection

    # We need a list to keep track of past lineups in order to enforce creation of unique lineups
    past_selections = [0] * (num_players * 2)

    with open(path + '%s lineups overlap %s.csv' % (date, lineup_overlap), 'w+', newline='') as lineups_csv:
        # Initialize CSV writer and write first row. This will contain the final lineups in DK format
        csv_writer = csv.writer(lineups_csv)
        csv_writer.writerow(['CAPT', 'FLEX', 'FLEX', 'FLEX', 'FLEX', 'FLEX'])

        # Generate lineups
        for lineup_count in range(0, num_lineups):
            # Constraint to limit overlap with previously generated lineups
            past_lineups_constraint = past_selections @ selection <= lineup_overlap

            # Add rule constraints
            constraints = [players_constraint, salary_constraint, flex_constraint, captain_constraint,
                           past_lineups_constraint]
            constraints.extend(captain_constraint_list)
            constraints.extend(team_stack_constraints)

            # Formulate problem and solve
            problem = cvxpy.Problem(cvxpy.Maximize(total_pts), constraints)
            problem.solve(solver=cvxpy.GLPK_MI)
            if problem.solution.status == 'infeasible':
                print('Problem formulation is infeasible.')
                return
            solution_array = problem.solution.primal_vars[selection.id]

            captain_index = 0
            flex_index = 1
            row = [''] * 6
            for i in range(0, len(solution_array)):
                if solution_array[i] == 1:
                    player = players.iloc[i]
                    if i < num_players:
                        row[flex_index] = player['Name']
                        flex_index += 1
                    else:
                        row[captain_index] = player['Name']
                        break
            csv_writer.writerow(row)

            # Add lineup to past selections in order to create unique lineups
            past_selections = np.logical_or(solution_array, past_selections)
