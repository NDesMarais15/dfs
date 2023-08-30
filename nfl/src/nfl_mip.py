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
        qb_team_matrix = np.zeros((len(teams), num_players))
        rb_team_matrix = np.zeros((len(teams), num_players))
        receiver_team_matrix = np.zeros((len(teams), num_players))
        def_team_matrix = np.zeros((len(teams), num_players))
        qb_opp_matrix = np.zeros((len(teams), num_players))
        opp_matrix = np.zeros((len(teams), num_players))

        # We need matrices of players that map team to position for the stacking constraints
        for j in range(0, len(teams)):
            for k in range(0, len(players)):
                if players.iloc[k]['Team'] == teams[j]:
                    if players.iloc[k]['Pos'] == 'QB':
                        qb_team_matrix[j][k] = 1

                    # Include both WRs and TEs as "receivers" for the stacking constraint
                    elif players.iloc[k]['Pos'] == 'WR' or players.iloc[k]['Pos'] == 'TE':
                        receiver_team_matrix[j][k] = 1

                    elif players.iloc[k]['Pos'] == 'RB':
                        rb_team_matrix[j][k] = 1

                    elif players.iloc[k]['Pos'] == 'DST':
                        def_team_matrix[j][k] = 1

                elif players.iloc[k]['Opp'] == teams[j]:
                    opp_matrix[j][k] = 1

                    if players.iloc[k]['Pos'] == 'QB':
                        qb_opp_matrix[j][k] = 1

        # Initialize CSV writer and write first row. This will contain the final lineups in DK format
        csv_writer = writer(lineups_csv)
        csv_writer.writerow(['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'TE', 'FLEX', 'DST'])

        # Create rows for players to easily map their position
        # FLEX not included since that can be used for RB, WR, or TE
        players['QB'] = 0
        players.loc[players['Pos'] == 'QB', 'QB'] = 1

        players['WR'] = 0
        players.loc[players['Pos'] == 'WR', 'WR'] = 1

        players['RB'] = 0
        players.loc[players['Pos'] == 'RB', 'RB'] = 1

        players['TE'] = 0
        players.loc[players['Pos'] == 'TE', 'TE'] = 1

        players['DST'] = 0
        players.loc[players['Pos'] == 'DST', 'DST'] = 1

        # We need a list to keep track of past lineups in order to enforce creation of unique lineups
        past_lineup_constraints = []

        # This is just a list of all ones in order to ensure that the number of players is 9
        ones = [1] * num_players

        # Variable for which players we ultimately select in a given lineup
        selection = cvxpy.Variable(num_players, boolean=True)

        # Total salary must not exceed $50,000
        salary_constraint = players['Salary'].to_numpy() @ selection <= 50000

        # Only one QB
        qb_constraint = players['QB'].to_numpy() @ selection == 1

        # At least 2 RBs, but no more than 3 (to account for FLEX)
        rb_constraint_1 = players['RB'].to_numpy() @ selection >= 2
        rb_constraint_2 = players['RB'].to_numpy() @ selection <= 3

        # At least 3 WRs, but no more than 4 (to account for FLEX)
        wr_constraint_1 = players['WR'].to_numpy() @ selection >= 3
        wr_constraint_2 = players['WR'].to_numpy() @ selection <= 4

        # At least 1 TE, but no more than 2 (to account for FLEX)
        te_constraint_1 = players['TE'].to_numpy() @ selection >= 1
        te_constraint_2 = players['TE'].to_numpy() @ selection <= 2

        # Exactly one defense/special teams selection
        dst_constraint = players['DST'].to_numpy() @ selection == 1

        # Must have exactly 9 players in a lineup. This is a DK constraint
        players_constraint = ones @ selection == 9

        # We add stacking constraints to a list because they are on a per team basis,
        # so there are a variable amount depending on how many teams are in the slate
        team_stack_constraints = []
        for i in range(0, len(qb_team_matrix)):
            # 2 receivers matched up with the QB. Receiver in this context allows for TEs
            if '2R' in strategy:
                team_stack_constraints.append(((qb_team_matrix[i] @ selection) * 2)
                                              <= (receiver_team_matrix[i] @ selection))

            # 1 receiver matched up with the QB. Receiver in this context allows for TEs
            if '1R' in strategy:
                team_stack_constraints.append((qb_team_matrix[i] @ selection)
                                              <= (receiver_team_matrix[i] @ selection))

            # At least 1 receiver from the QB's opposing team. Idea is that in a high scoring game,
            # both teams will be passing a lot, and receivers from either team will do well
            if '1OppR' in strategy:
                team_stack_constraints.append((qb_opp_matrix[i] @ selection) <= (receiver_team_matrix[i] @ selection))

            # QB cannot play against his own defense. QB's points are negatively correlated
            # with his opponent's points. Uses Big M constraint
            if 'NoQBvsDef' in strategy:
                team_stack_constraints.append(((def_team_matrix[i] @ selection) * 1000) + (qb_opp_matrix[i] @ selection)
                                              <= 1000)

            # No player can play against his own defense. Any offensive player's points are
            # going to be negatively correlated, but this might be a little too restrictive.
            # More testing is necessary to reach a verdict. Uses Big M constraint
            elif 'NoPlayervsDef' in strategy:
                team_stack_constraints.append(((def_team_matrix[i] @ selection) * 1000) + (opp_matrix[i] @ selection)
                                              <= 1000)

            # QB cannot be paired with a RB. Idea is that rushing and passing are negatively correlated;
            # however, some RBs are active in the passing game as well. Could potentially make this more
            # nuanced in the future, e.g. only allow running backs who average a certain number of
            # receptions
            if 'NoQB&RB' in strategy:
                team_stack_constraints.append(((qb_team_matrix[i] @ selection) * 1000) + (rb_team_matrix[i] @ selection)
                                              <= 1000)

            # No two running backs from the same team. RBs compete for carries, so including two
            # from the same team limits upside.
            if 'NoRB&RB' in strategy:
                team_stack_constraints.append((rb_team_matrix[i] @ selection) <= 1)

        # Total number of projected fantasy points. This is what we are maximizing
        total_pts = players['Proj_FP'].to_numpy() @ selection

        # Generate lineups
        for lineup_count in range(0, num_lineups):
            # Add rule constraints
            constraints = [salary_constraint, qb_constraint, rb_constraint_1, rb_constraint_2, wr_constraint_1,
                           wr_constraint_2, te_constraint_1, te_constraint_2, dst_constraint, players_constraint]

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

            # The solution array is a matrix of players in the order we collected them from
            # rotogrinders, so we have to do some work to actually write the lineups in a
            # way that will be readable by humans and eventually DraftKings
            qb_index = 0
            rb_index = 1
            wr_index = 3
            te_index = 6
            flex_index = 7
            dst_index = 8
            row = [''] * 9
            for i in range(0, len(solution_array)):
                if solution_array[i] == 1:
                    player = players.iloc[i]
                    if player['Pos'] == 'QB':
                        row[qb_index] = player['Player_Name']
                    elif player['Pos'] == 'RB':
                        if rb_index == 3:
                            rb_index = flex_index
                        row[rb_index] = player['Player_Name']
                        rb_index += 1
                    elif player['Pos'] == 'WR':
                        if wr_index == 6:
                            wr_index = flex_index
                        row[wr_index] = player['Player_Name']
                        wr_index += 1
                    elif player['Pos'] == 'TE':
                        row[te_index] = player['Player_Name']
                        te_index += 1
                    elif player['Pos'] == 'DST':
                        row[dst_index] = player['Player_Name']
            csv_writer.writerow(row)

            # Add lineup to past selections in order to create unique lineups
            past_lineup_constraints.append(solution_array @ selection <= lineup_overlap)


def generate_showdown_lineups(date, projections_path, lineup_path, num_lineups, lineup_overlap, strategy):
    with open(projections_path + '%s projections.csv' % date, 'r') as players_csv:
        players = pd.read_csv(players_csv)

    teams = players['Team'].unique()
    num_players = len(players['Salary'])

    # Variable for which players we ultimately select in a given lineup
    selection = cvxpy.Variable(num_players * 2, boolean=True)

    captain_list = []
    captain_constraint_list = []
    for (index, player) in players.iterrows():
        player_dict = {'Player_Name': player['Player_Name'],
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

    # Total number of projected fantasy points. This is what we are maximizing
    total_pts = players['Proj_FP'].to_numpy() @ selection

    # Initialize matrices (num_teams x num_players)
    player_team_matrix = np.zeros((len(teams), num_players * 2))
    qb_team_matrix = np.zeros((len(teams), num_players * 2))
    rb_team_matrix = np.zeros((len(teams), num_players * 2))
    receiver_team_matrix = np.zeros((len(teams), num_players * 2))
    def_team_matrix = np.zeros((len(teams), num_players * 2))
    qb_opp_matrix = np.zeros((len(teams), num_players * 2))
    opp_matrix = np.zeros((len(teams), num_players * 2))

    # We need matrices of players that map team to position for the stacking constraints
    for j in range(0, len(teams)):
        for k in range(0, len(players)):
            if players.iloc[k]['Team'] == teams[j]:
                player_team_matrix[j][k] = 1
                if players.iloc[k]['Pos'] == 'QB':
                    qb_team_matrix[j][k] = 1

                # Include both WRs and TEs as "receivers" for the stacking constraint
                elif players.iloc[k]['Pos'] == 'WR' or players.iloc[k]['Pos'] == 'TE':
                    receiver_team_matrix[j][k] = 1

                elif players.iloc[k]['Pos'] == 'RB':
                    rb_team_matrix[j][k] = 1

                elif players.iloc[k]['Pos'] == 'DST':
                    def_team_matrix[j][k] = 1

            elif players.iloc[k]['Opp'] == teams[j]:
                opp_matrix[j][k] = 1

                if players.iloc[k]['Pos'] == 'QB':
                    qb_opp_matrix[j][k] = 1

    # We add stacking constraints to a list because they are on a per team basis,
    # so there are a variable amount depending on how many teams are in the slate
    team_stack_constraints = []
    for i in range(0, len(qb_team_matrix)):
        # Must have at least one player from each team
        team_stack_constraints.append(player_team_matrix[i] @ selection >= 1)

        # 2 receivers matched up with the QB. Receiver in this context allows for TEs
        if '2R' in strategy:
            team_stack_constraints.append(((qb_team_matrix[i] @ selection) * 2)
                                          <= (receiver_team_matrix[i] @ selection))

        # At least 1 receiver from the QB's opposing team. Idea is that in a high scoring game,
        # both teams will be passing a lot, and receivers from either team will do well
        if '1OppR' in strategy:
            team_stack_constraints.append((qb_opp_matrix[i] @ selection) <= (receiver_team_matrix[i] @ selection))

        # QB cannot play against his own defense. QB's points are negatively correlated
        # with his opponent's points. Uses Big M constraint
        if 'NoQBvsDef' in strategy:
            team_stack_constraints.append(((def_team_matrix[i] @ selection) * 1000) + (qb_opp_matrix[i] @ selection)
                                          <= 1000)

        # No player can play against his own defense. Any offensive player's points are
        # going to be negatively correlated, but this might be a little too restrictive.
        # More testing is necessary to reach a verdict. Uses Big M constraint
        elif 'NoPlayervsDef' in strategy:
            team_stack_constraints.append(((def_team_matrix[i] @ selection) * 1000) + (opp_matrix[i] @ selection)
                                          <= 1000)

        # QB cannot be paired with a RB. Idea is that rushing and passing are negatively correlated;
        # however, some RBs are active in the passing game as well. Could potentially make this more
        # nuanced in the future, e.g. only allow running backs who average a certain number of
        # receptions
        if 'NoQB&RB' in strategy:
            team_stack_constraints.append(((qb_team_matrix[i] @ selection) * 1000) + (rb_team_matrix[i] @ selection)
                                          <= 1000)

        # No two running backs from the same team. RBs compete for carries, so including two
        # from the same team limits upside.
        if 'NoRB&RB' in strategy:
            team_stack_constraints.append((rb_team_matrix[i] @ selection) <= 1)

    # We need a list to keep track of past lineups in order to enforce creation of unique lineups
    past_lineup_constraints = []

    with open(lineup_path + '%s lineups overlap %s.csv' % (date, lineup_overlap), 'w+', newline='') as lineups_csv:
        # Initialize CSV writer and write first row. This will contain the final lineups in DK format
        csv_writer = writer(lineups_csv)
        csv_writer.writerow(['CAPT', 'FLEX', 'FLEX', 'FLEX', 'FLEX', 'FLEX'])

        # Generate lineups
        for lineup_count in range(0, num_lineups):
            # Add rule constraints
            constraints = [players_constraint, salary_constraint, flex_constraint, captain_constraint]
            constraints.extend(captain_constraint_list)
            constraints.extend(team_stack_constraints)
            constraints.extend(past_lineup_constraints)

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
                        row[flex_index] = player['Player_Name']
                        flex_index += 1
                    else:
                        row[captain_index] = player['Player_Name']
                        break
            csv_writer.writerow(row)

            # Add lineup to past selections in order to create unique lineups
            past_lineup_constraints.append(solution_array @ selection <= lineup_overlap)
