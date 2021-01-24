#=
This code implements the No Stacking, Type 1, Type 2, Type 3, Type 4, and Type 5 formulations
described in the paper Winning Daily Fantasy Hockey Contests Using Integer Programming by
Hunter, Vielma, and Zaman. We have made an attempt to describe the code in great detail, with the
hope that you will use your expertise to build better formulations.
=#

start = time()

# To install DataFrames, simply run Pkg.add("DataFrames")
using DataFrames
using TimeZones

#=
GLPK is an open-source solver, and additionally Cbc is an open-source solver. This code uses GLPK
because we found that it was slightly faster than Cbc in practice. For those that want to build
very sophisticated models, they can buy Gurobi. To install GLPKMathProgInterface, simply run
Pkg.add("GLPKMathProgInterface")
=#
using GLPKMathProgInterface
using GLPK

# Once again, to install run Pkg.add("JuMP")
using JuMP

using Printf
using CSV

#=
Variables for solving the problem (change these)
=#
# num_lineups is the total number of lineups
num_lineups = 20

# num_overlap is the maximum overlap of players between the lineups that you create
num_overlap = 7

# path_players is a string that gives the path to the csv file with the players information (see example file for suggested format)
path_players = "$(TimeZones.today(tz"America/Chicago")) projections.csv"

# path_to_output is a string that gives the path to the csv file that will give the outputted results
path_to_output = "$(TimeZones.today(tz"America/Chicago")) lineup overlap $(num_overlap).csv"

# This is a function that creates one lineup using the No Stacking formulation from the paper
function one_lineup_no_stacking(skaters, goalies, lineups, num_overlap, num_skaters, num_goalies, centers, wingers, defenders, num_teams, skaters_teams, goalie_opponents, team_lines, num_lines, P1_info)
    m = Model(with_optimizer(GLPK.Optimizer))

    # Variable for skaters in lineup.
    @variable(m, skaters_lineup[i=1:num_skaters], Bin)

    # Variable for goalie in lineup.
    @variable(m, goalies_lineup[i=1:num_goalies], Bin)


    # One goalie constraint
    @constraint(m, sum(goalies_lineup[i] for i in 1:num_goalies) == 1)

    # Eight Skaters constraint
    @constraint(m, sum(skaters_lineup[i] for i in 1:num_skaters) == 8)

    # between 2 and 3 centers
    @constraint(m, sum(centers[i]*skaters_lineup[i] for i in 1:num_skaters) <= 3)
    @constraint(m, 2 <= sum(centers[i]*skaters_lineup[i] for i in 1:num_skaters))

    # between 3 and 4 wingers
    @constraint(m, sum(wingers[i]*skaters_lineup[i] for i in 1:num_skaters) <= 4)
    @constraint(m, 3<=sum(wingers[i]*skaters_lineup[i] for i in 1:num_skaters))

    # between 2 and 3 defenders
    @constraint(m, 2 <= sum(defenders[i]*skaters_lineup[i] for i in 1:num_skaters))
    @constraint(m, sum(defenders[i]*skaters_lineup[i] for i in 1:num_skaters) <= 3)

    # Financial Constraint
    @constraint(m, sum(skaters[i,:Salary]*skaters_lineup[i] for i in 1:num_skaters) + sum(goalies[i,:Salary]*goalies_lineup[i] for i in 1:num_goalies) <= 50000)

    # at least 3 different teams for the 8 skaters constraints
    @variable(m, used_team[i=1:num_teams], Bin)
    @constraint(m, [i=1:num_teams], used_team[i] <= sum(skaters_teams[t, i]*skaters_lineup[t] for t in 1:num_skaters))
    @constraint(m, sum(used_team[i] for i in 1:num_teams) >= 3)

    # Overlap Constraint
    @constraint(m, [i=1:size(lineups)[2]], sum(lineups[j,i]*skaters_lineup[j] for j in 1:num_skaters) + sum(lineups[num_skaters+j,i]*goalies_lineup[j] for j in 1:num_goalies) <= num_overlap)


    # Objective
    @objective(m, Max, sum(skaters[i,:Proj_FP]*skaters_lineup[i] for i in 1:num_skaters) + sum(goalies[i,:Proj_FP]*goalies_lineup[i] for i in 1:num_goalies))


    # Solve the integer programming problem
    start = time()
    optimize!(m)
    println("Generated lineup in $(time() - start) seconds")
    status = termination_status(m);

    # Puts the output of one lineup into a format that will be used later
    if status==MOI.OPTIMAL
        skaters_lineup_copy = Array{Int64}(undef, 0)
        for i=1:num_skaters
            if value(skaters_lineup[i]) >= 0.9 && value(skaters_lineup[i]) <= 1.1
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(1,1))
            else
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(0,1))
            end
        end
        for i=1:num_goalies
            if value(goalies_lineup[i]) >= 0.9 && value(goalies_lineup[i]) <= 1.1
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(1,1))
            else
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(0,1))
            end
        end
        return(skaters_lineup_copy)
    end
end





# This is a function that creates one lineup using the Type 1 formulation from the paper
function one_lineup_Type_1(skaters, goalies, lineups, num_overlap, num_skaters, num_goalies, centers, wingers, defenders, num_teams, skaters_teams, goalie_opponents, team_lines, num_lines, P1_info)
    m = Model(with_optimizer(GLPK.Optimizer))

    # Variable for skaters in lineup
    @variable(m, skaters_lineup[i=1:num_skaters], Bin)

    # Variable for goalie in lineup
    @variable(m, goalies_lineup[i=1:num_goalies], Bin)


    # One goalie constraint
    @constraint(m, sum(goalies_lineup[i] for i in 1:num_goalies) == 1)

    # Eight skaters constraint
    @constraint(m, sum(skaters_lineup[i] for i in 1:num_skaters) == 8)


    # between 2 and 3 centers
    @constraint(m, sum(centers[i]*skaters_lineup[i] for i in 1:num_skaters) <= 3)
    @constraint(m, 2 <= sum(centers[i]*skaters_lineup[i] for i in 1:num_skaters))

    # between 3 and 4 wingers
    @constraint(m, sum(wingers[i]*skaters_lineup[i] for i in 1:num_skaters) <= 4)
    @constraint(m, 3<=sum(wingers[i]*skaters_lineup[i] for i in 1:num_skaters))

    # between 2 and 3 defenders
    @constraint(m, 2 <= sum(defenders[i]*skaters_lineup[i] for i in 1:num_skaters))
    @constraint(m, sum(defenders[i]*skaters_lineup[i] for i in 1:num_skaters) <= 3)


    # Financial Constraint
    @constraint(m, sum(skaters[i,:Salary]*skaters_lineup[i] for i in 1:num_skaters) + sum(goalies[i,:Salary]*goalies_lineup[i] for i in 1:num_goalies) <= 50000)


    # At least 3 different teams for the 8 skaters constraint
    @variable(m, used_team[i=1:num_teams], Bin)
    @constraint(m, [i=1:num_teams], used_team[i] <= sum(skaters_teams[t, i]*skaters_lineup[t] for t in 1:num_skaters))
    @constraint(m, sum(used_team[i] for i in 1:num_teams) >= 3)


    # No goalies going against skaters constraint
    @constraint(m, [i=1:num_goalies], 6*goalies_lineup[i] + sum(goalie_opponents[k, i]*skaters_lineup[k] for k in 1:num_skaters) <= 6)


    # Must have at least one complete line in each lineup
    @variable(m, line_stack[i=1:num_lines], Bin)
    @constraint(m, [i=1:num_lines], 3*line_stack[i] <= sum(team_lines[k,i]*skaters_lineup[k] for k in 1:num_skaters))
    @constraint(m, sum(line_stack[i] for i in 1:num_lines) >= 1)


    # Must have at least 2 lines with at least two people
    @variable(m, line_stack2[i=1:num_lines], Bin)
    @constraint(m, [i=1:num_lines], 2*line_stack2[i] <= sum(team_lines[k,i]*skaters_lineup[k] for k in 1:num_skaters))
    @constraint(m, sum(line_stack2[i] for i in 1:num_lines) >= 2)


    # Overlap Constraint
    @constraint(m, [i=1:size(lineups)[2]], sum(lineups[j,i]*skaters_lineup[j] for j in 1:num_skaters) + sum(lineups[num_skaters+j,i]*goalies_lineup[j] for j in 1:num_goalies) <= num_overlap)


    # Objective
    @objective(m, Max, sum(skaters[i,:Proj_FP]*skaters_lineup[i] for i in 1:num_skaters) + sum(goalies[i,:Proj_FP]*goalies_lineup[i] for i in 1:num_goalies))


    # Solve the integer programming problem
    start = time()
    optimize!(m)
    println("Generated lineup in $(time() - start) seconds")
    status = termination_status(m);


    # Puts the output of one lineup into a format that will be used later
    if status==MOI.OPTIMAL
        skaters_lineup_copy = Array{Int64}(undef, 0)
        for i=1:num_skaters
            if value(skaters_lineup[i]) >= 0.9 && value(skaters_lineup[i]) <= 1.1
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(1,1))
            else
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(0,1))
            end
        end
        for i=1:num_goalies
            if value(goalies_lineup[i]) >= 0.9 && value(goalies_lineup[i]) <= 1.1
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(1,1))
            else
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(0,1))
            end
        end
        return(skaters_lineup_copy)
    end
end


# This is a function that creates one lineup using the Type 2 formulation from the paper
function one_lineup_Type_2(skaters, goalies, lineups, num_overlap, num_skaters, num_goalies, centers, wingers, defenders, num_teams, skaters_teams, goalie_opponents, team_lines, num_lines, P1_info)
    m = Model(with_optimizer(GLPK.Optimizer))

    # Variable for skaters in lineup
    @variable(m, skaters_lineup[i=1:num_skaters], Bin)

    # Variable for goalie in lineup
    @variable(m, goalies_lineup[i=1:num_goalies], Bin)

    # One goalie constraint
    @constraint(m, sum(goalies_lineup[i] for i in 1:num_goalies) == 1)

    # Eight skaters constraint
    @constraint(m, sum(skaters_lineup[i] for i in 1:num_skaters) == 8)

    # between 2 and 3 centers
    @constraint(m, sum(centers[i]*skaters_lineup[i] for i in 1:num_skaters) <= 3)
    @constraint(m, 2 <= sum(centers[i]*skaters_lineup[i] for i in 1:num_skaters))

    # between 3 and 4 wingers
    @constraint(m, sum(wingers[i]*skaters_lineup[i] for i in 1:num_skaters) <= 4)
    @constraint(m, 3<=sum(wingers[i]*skaters_lineup[i] for i in 1:num_skaters))

    # exactly 2 defenders
    @constraint(m, 2 == sum(defenders[i]*skaters_lineup[i] for i in 1:num_skaters))

    # Financial Constraint
    @constraint(m, sum(skaters[i,:Salary]*skaters_lineup[i] for i in 1:num_skaters) + sum(goalies[i,:Salary]*goalies_lineup[i] for i in 1:num_goalies) <= 50000)

    # at least 3 different teams for the 8 skaters constraint
    @variable(m, used_team[i=1:num_teams], Bin)
    @constraint(m, [i=1:num_teams], used_team[i] <= sum(skaters_teams[t, i]*skaters_lineup[t] for t in 1:num_skaters))
    @constraint(m, sum(used_team[i] for i in 1:num_teams) >= 3)

    # No goalies going against skaters constraint
    @constraint(m, [i=1:num_goalies], 6*goalies_lineup[i] + sum(goalie_opponents[k, i]*skaters_lineup[k] for k in 1:num_skaters)<=6)

    # Must have at least one complete line in each lineup
    @variable(m, line_stack[i=1:num_lines], Bin)
    @constraint(m, [i=1:num_lines], 3*line_stack[i] <= sum(team_lines[k,i]*skaters_lineup[k] for k in 1:num_skaters))
    @constraint(m, sum(line_stack[i] for i in 1:num_lines) >= 1)

    # Must have at least 2 lines with at least two people
    @variable(m, line_stack2[i=1:num_lines], Bin)
    @constraint(m, [i=1:num_lines], 2*line_stack2[i] <= sum(team_lines[k,i]*skaters_lineup[k] for k in 1:num_skaters))
    @constraint(m, sum(line_stack2[i] for i in 1:num_lines) >= 2)

    # Overlap Constraint
    @constraint(m, [i=1:size(lineups)[2]], sum(lineups[j,i]*skaters_lineup[j] for j in 1:num_skaters) + sum(lineups[num_skaters+j,i]*goalies_lineup[j] for j in 1:num_goalies) <= num_overlap)

    # Objective
    @objective(m, Max, sum(skaters[i,:Proj_FP]*skaters_lineup[i] for i in 1:num_skaters) + sum(goalies[i,:Proj_FP]*goalies_lineup[i] for i in 1:num_goalies))

    # Solve the integer programming problem
    start = time()
    optimize!(m)
    println("Generated lineup in $(time() - start) seconds")
    status = termination_status(m)

    # Puts the output of one lineup into a format that will be used later
    if status==MOI.OPTIMAL
        skaters_lineup_copy = Array{Int64}(undef, 0)
        for i=1:num_skaters
            if value(skaters_lineup[i]) >= 0.9 && value(skaters_lineup[i]) <= 1.1
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(1,1))
            else
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(0,1))
            end
        end
        for i=1:num_goalies
            if value(goalies_lineup[i]) >= 0.9 && value(goalies_lineup[i]) <= 1.1
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(1,1))
            else
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(0,1))
            end
        end
        return(skaters_lineup_copy)
    end
end


# This is a function that creates one lineup using the Type 3 formulation from the paper
function one_lineup_Type_3(skaters, goalies, lineups, num_overlap, num_skaters, num_goalies, centers, wingers, defenders, num_teams, skaters_teams, goalie_opponents, team_lines, num_lines, P1_info)
    m = Model(with_optimizer(GLPK.Optimizer))

    # Variable for skaters in lineup
    @variable(m, skaters_lineup[i=1:num_skaters], Bin)

    # Variable for goalie in lineup
    @variable(m, goalies_lineup[i=1:num_goalies], Bin)

    # One goalie constraint
    @constraint(m, sum(goalies_lineup[i] for i in 1:num_goalies) == 1)

    # Eight Skaters constraint
    @constraint(m, sum(skaters_lineup[i] for i in 1:num_skaters) == 8)

    # between 2 and 3 centers
    @constraint(m, sum(centers[i]*skaters_lineup[i] for i in 1:num_skaters) <= 3)
    @constraint(m, 2 <= sum(centers[i]*skaters_lineup[i] for i in 1:num_skaters))

    # between 3 and 4 wingers
    @constraint(m, sum(wingers[i]*skaters_lineup[i] for i in 1:num_skaters) <= 4)
    @constraint(m, 3<=sum(wingers[i]*skaters_lineup[i] for i in 1:num_skaters))

    # between 2 and 3 defenders
    @constraint(m, 2 <= sum(defenders[i]*skaters_lineup[i] for i in 1:num_skaters))
    @constraint(m, sum(defenders[i]*skaters_lineup[i] for i in 1:num_skaters) <= 3)

    # Financial Constraint
    @constraint(m, sum(skaters[i,:Salary]*skaters_lineup[i] for i in 1:num_skaters) + sum(goalies[i,:Salary]*goalies_lineup[i] for i in 1:num_goalies) <= 50000)

    # at least 3 different teams for the 8 skaters constraint
    @variable(m, used_team[i=1:num_teams], Bin)
    @constraint(m, [i=1:num_teams], used_team[i] <= sum(skaters_teams[t, i]*skaters_lineup[t] for t in 1:num_skaters))
    @constraint(m, sum(used_team[i] for i in 1:num_teams) >= 3)

    # No goalies going against skaters
    @constraint(m, [i=1:num_goalies], 6*goalies_lineup[i] + sum(goalie_opponents[k, i]*skaters_lineup[k] for k in 1:num_skaters)<=6)

    # Must have at least one complete line in each lineup
    @variable(m, line_stack[i=1:num_lines], Bin)
    @constraint(m, [i=1:num_lines], 3*line_stack[i] <= sum(team_lines[k,i]*skaters_lineup[k] for k in 1:num_skaters))
    @constraint(m, sum(line_stack[i] for i in 1:num_lines) >= 1)

    # Must have at least 2 lines with at least two people
    @variable(m, line_stack2[i=1:num_lines], Bin)
    @constraint(m, [i=1:num_lines], 2*line_stack2[i] <= sum(team_lines[k,i]*skaters_lineup[k] for k in 1:num_skaters))
    @constraint(m, sum(line_stack2[i] for i in 1:num_lines) >= 2)

    # The defenders must be on Power Play 1 constraint
    @constraint(m, sum(sum(defenders[i]*P1_info[i,j]*skaters_lineup[i] for i in 1:num_skaters) for j in 1:num_teams) == sum(defenders[i]*skaters_lineup[i] for i in 1:num_skaters))

    # Overlap Constraint
    @constraint(m, [i=1:size(lineups)[2]], sum(lineups[j,i]*skaters_lineup[j] for j in 1:num_skaters) + sum(lineups[num_skaters+j,i]*goalies_lineup[j] for j in 1:num_goalies) <= num_overlap)

    # Objective
    @objective(m, Max, sum(skaters[i,:Proj_FP]*skaters_lineup[i] for i in 1:num_skaters) + sum(goalies[i,:Proj_FP]*goalies_lineup[i] for i in 1:num_goalies))

    # Solve the integer programming problem
    start = time()
    optimize!(m)
    println("Generated lineup in $(time() - start) seconds")
    status = termination_status(m);

    # Puts the output of one lineup into a format that will be used later
    if status==MOI.OPTIMAL
        skaters_lineup_copy = Array{Int64}(undef, 0)
        for i=1:num_skaters
            if value(skaters_lineup[i]) >= 0.9 && value(skaters_lineup[i]) <= 1.1
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(1,1))
            else
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(0,1))
            end
        end
        for i=1:num_goalies
            if value(goalies_lineup[i]) >= 0.9 && value(goalies_lineup[i]) <= 1.1
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(1,1))
            else
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(0,1))
            end
        end
        return(skaters_lineup_copy)
    end
end




# This is a function that creates one lineup using the Type 4 formulation from the paper
function one_lineup_Type_4(skaters, goalies, lineups, num_overlap, num_skaters, num_goalies, centers, wingers, defenders, num_teams, skaters_teams, goalie_opponents, team_lines, num_lines, P1_info)
    m = Model(with_optimizer(GLPK.Optimizer))

    # Variable for skaters in lineup
    @variable(m, skaters_lineup[i=1:num_skaters], Bin)

    # Variable for goalie in lineup
    @variable(m, goalies_lineup[i=1:num_goalies], Bin)

    # One goalie constraint
    @constraint(m, sum(goalies_lineup[i] for i in 1:num_goalies) == 1)

    # Eight Skaters constraint
    @constraint(m, sum(skaters_lineup[i] for i in 1:num_skaters) == 8)

    # between 2 and 3 centers
    @constraint(m, sum(centers[i]*skaters_lineup[i] for i in 1:num_skaters) <= 3)
    @constraint(m, 2 <= sum(centers[i]*skaters_lineup[i] for i in 1:num_skaters))

    # between 3 and 4 wingers
    @constraint(m, sum(wingers[i]*skaters_lineup[i] for i in 1:num_skaters) <= 4)
    @constraint(m, 3 <= sum(wingers[i]*skaters_lineup[i] for i in 1:num_skaters))

    # between 2 and 3 defenders
    @constraint(m, 2 <= sum(defenders[i]*skaters_lineup[i] for i in 1:num_skaters))
    @constraint(m, sum(defenders[i]*skaters_lineup[i] for i in 1:num_skaters) <= 3)

    # Financial Constraint
    @constraint(m, sum(skaters[i,:Salary]*skaters_lineup[i] for i in 1:num_skaters) + sum(goalies[i,:Salary]*goalies_lineup[i] for i in 1:num_goalies) <= 50000)

    # exactly 3 different teams for the 8 skaters constraint
    @variable(m, used_team[i=1:num_teams], Bin)
    @constraint(m, [i=1:num_teams], sum(skaters_teams[t, i]*skaters_lineup[t] for t in 1:num_skaters) >= used_team[i])
    @constraint(m, [i=1:num_teams], sum(skaters_teams[t, i]*skaters_lineup[t] for t in 1:num_skaters) <= 6*used_team[i])
    @constraint(m, sum(used_team[i] for i in 1:num_teams) == 3)

    # No goalies going against skaters
    @constraint(m, [i=1:num_goalies], 6*goalies_lineup[i] + sum(goalie_opponents[k, i]*skaters_lineup[k] for k in 1:num_skaters)<=6)

    # Must have at least one complete line in each lineup
    @variable(m, line_stack[i=1:num_lines], Bin)
    @constraint(m, [i=1:num_lines], 3*line_stack[i] <= sum(team_lines[k,i]*skaters_lineup[k] for k in 1:num_skaters))
    @constraint(m, sum(line_stack[i] for i in 1:num_lines) >= 1)

    # Must have at least 2 lines with at least two people
    @variable(m, line_stack2[i=1:num_lines], Bin)
    @constraint(m, [i=1:num_lines], 2*line_stack2[i] <= sum(team_lines[k,i]*skaters_lineup[k] for k in 1:num_skaters))
    @constraint(m, sum(line_stack2[i] for i in 1:num_lines) >= 2)

    # The defenders must be on Power Play 1
    @constraint(m, sum(sum(defenders[i]*P1_info[i,j]*skaters_lineup[i] for i in 1:num_skaters) for j in 1:num_teams) == sum(defenders[i]*skaters_lineup[i] for i in 1:num_skaters))

    # Overlap Constraint
    @constraint(m, [i=1:size(lineups)[2]], sum(lineups[j,i]*skaters_lineup[j] for j in 1:num_skaters) + sum(lineups[num_skaters+j,i]*goalies_lineup[j] for j in 1:num_goalies) <= num_overlap)

    # Objective
    @objective(m, Max, (sum(skaters[i,:Proj_FP]*skaters_lineup[i] for i in 1:num_skaters) + sum(goalies[i,:Proj_FP]*goalies_lineup[i] for i in 1:num_goalies)))

    # Solve the integer programming problem
    start = time()
    optimize!(m)
    println("Generated lineup in $(time() - start) seconds")
    status = termination_status(m)

    # Puts the output of one lineup into a format that will be used later
    if status==MOI.OPTIMAL
        skaters_lineup_copy = Array{Int64}(undef, 0)
        for i=1:num_skaters
            if value(skaters_lineup[i]) >= 0.9 && value(skaters_lineup[i]) <= 1.1
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(1,1))
            else
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(0,1))
            end
        end
        for i=1:num_goalies
            if value(goalies_lineup[i]) >= 0.9 && value(goalies_lineup[i]) <= 1.1
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(1,1))
            else
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(0,1))
            end
        end
        return(skaters_lineup_copy)
    else
        println(status)
        println(primal_status(m))
    end
end


# This is a function that creates one lineup using the Type 5 formulation from the paper
function one_lineup_Type_5(skaters, goalies, lineups, num_overlap, num_skaters, num_goalies, centers, wingers, defenders, num_teams, skaters_teams, goalie_opponents, team_lines, num_lines, P1_info)
    m = Model(with_optimizer(GLPK.Optimizer))

    # Variable for skaters in lineup
    @variable(m, skaters_lineup[i=1:num_skaters], Bin)

    # Variable for goalie in lineup
    @variable(m, goalies_lineup[i=1:num_goalies], Bin)

    # One goalie constraint
    @constraint(m, sum(goalies_lineup[i] for i in 1:num_goalies) == 1)

    # Eight skaters constraint
    @constraint(m, sum(skaters_lineup[i] for i in 1:num_skaters) == 8)

    # between 2 and 3 centers
    @constraint(m, sum(centers[i]*skaters_lineup[i] for i in 1:num_skaters) <= 3)
    @constraint(m, 2 <= sum(centers[i]*skaters_lineup[i] for i in 1:num_skaters))

    # between 3 and 4 wingers
    @constraint(m, sum(wingers[i]*skaters_lineup[i] for i in 1:num_skaters) <= 4)
    @constraint(m, 3<=sum(wingers[i]*skaters_lineup[i] for i in 1:num_skaters))

    # between 2 and 3 defenders
    @constraint(m, 2 <= sum(defenders[i]*skaters_lineup[i] for i in 1:num_skaters))
    @constraint(m, sum(defenders[i]*skaters_lineup[i] for i in 1:num_skaters) <= 3)

    # Financial Constraint
    @constraint(m, sum(skaters[i,:Salary]*skaters_lineup[i] for i in 1:num_skaters) + sum(goalies[i,:Salary]*goalies_lineup[i] for i in 1:num_goalies) <= 50000)

    # exactly 3 different teams for the 8 skaters constraint
    @variable(m, used_team[i=1:num_teams], Bin)
    @constraint(m, [i=1:num_teams], used_team[i] <= sum(skaters_teams[t, i]*skaters_lineup[t] for t in 1:num_skaters))
    @constraint(m, [i=1:num_teams], sum(skaters_teams[t, i]*skaters_lineup[t] for t in 1:num_skaters) <= 6*used_team[i])
    @constraint(m, sum(used_team[i] for i in 1:num_teams) == 3)

    # No goalies going against skaters
    @constraint(m, [i=1:num_goalies], 6*goalies_lineup[i] + sum(goalie_opponents[k, i]*skaters_lineup[k] for k in 1:num_skaters)<=6)

    # Must have at least one complete line in each lineup
    @variable(m, line_stack[i=1:num_lines], Bin)
    @constraint(m, [i=1:num_lines], 3*line_stack[i] <= sum(team_lines[k,i]*skaters_lineup[k] for k in 1:num_skaters))
    @constraint(m, sum(line_stack[i] for i in 1:num_lines) >= 1)

    # Must have at least 2 lines with at least two people
    @variable(m, line_stack2[i=1:num_lines], Bin)
    @constraint(m, [i=1:num_lines], 2*line_stack2[i] <= sum(team_lines[k,i]*skaters_lineup[k] for k in 1:num_skaters))
    @constraint(m, sum(line_stack2[i] for i in 1:num_lines) >= 2)

    # Overlap Constraint
    @constraint(m, [i=1:size(lineups)[2]], sum(lineups[j,i]*skaters_lineup[j] for j in 1:num_skaters) + sum(lineups[num_skaters+j,i]*goalies_lineup[j] for j in 1:num_goalies) <= num_overlap)

    # Objective
    @objective(m, Max, sum(skaters[i,:Proj_FP]*skaters_lineup[i] for i in 1:num_skaters) + sum(goalies[i,:Proj_FP]*goalies_lineup[i] for i in 1:num_goalies))

    # Solve the integer programming problem
    start = time()
    optimize!(m)
    println("Generated lineup in $(time() - start) seconds")
    status = termination_status(m);

    # Puts the output of one lineup into a format that will be used later
    if status==MOI.OPTIMAL
        skaters_lineup_copy = Array{Int64}(undef, 0)
        for i=1:num_skaters
            if value(skaters_lineup[i]) >= 0.9 && value(skaters_lineup[i]) <= 1.1
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(1,1))
            else
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(0,1))
            end
        end
        for i=1:num_goalies
            if value(goalies_lineup[i]) >= 0.9 && value(goalies_lineup[i]) <= 1.1
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(1,1))
            else
                skaters_lineup_copy = vcat(skaters_lineup_copy, fill(0,1))
            end
        end
        return(skaters_lineup_copy)
    end
end

#=
formulation is the type of formulation that you would like to use. Feel free to customize the formulations. In our paper we considered
the Type 4 formulation in great detail, but we have included the code for all of the formulations dicussed in the paper here. For instance,
if you would like to create lineups without stacking, change one_lineup_Type_4 below to one_lineup_no_stacking
=#
formulation = one_lineup_Type_4

function create_lineups(num_lineups, num_overlap, path_players, formulation, path_to_output)
    #=
    num_lineups is an integer that is the number of lineups
    num_overlap is an integer that gives the overlap between each lineup
    path_players is a string that gives the path to the players csv file
    formulation is the type of formulation you would like to use (for instance one_lineup_Type_1, one_lineup_Type_2, etc.)
    path_to_output is a string where the final csv file with your lineups will be
    =#

    # Load information for players table
    players = CSV.read(path_players, copycols=true)

    select!(players, [:Name, :Pos, :Line, :PP_Line,
        :Team, :Opp, :Salary, :Proj_FP])

    # Number of players
    num_players = size(players)[1]

    # wingers stores the information on which players are wings
    wingers = Array{Int64}(undef, 0)

    # centers stores the information on which players are centers
    centers = Array{Int64}(undef, 0)

    # defenders stores the information on which players are defenders
    defenders = Array{Int64}(undef, 0)

    # goalies stores the information on which players are goalies
    goalies = DataFrame(Name = Array{String}(undef, 0),
                        Salary = Array{Int64}(undef, 0),
                        Team = Array{String}(undef, 0),
                        Opp = Array{String}(undef, 0),
                        Proj_FP = Array{Float64}(undef, 0))

    goalie_indices = Array{Int64}(undef, 0)

    #=
    Process the Pos information in the skaters file to populate the wingers,
    centers, and defenders with the corresponding correct information
    =#
    for i=1:num_players
        if players[i,:Pos] == "LW" || players[i,:Pos] == "RW" || players[i,:Pos] == "W"
            wingers=vcat(wingers,fill(1,1))
            centers=vcat(centers,fill(0,1))
            defenders=vcat(defenders,fill(0,1))
        elseif players[i,:Pos] == "C"
            wingers=vcat(wingers,fill(0,1))
            centers=vcat(centers,fill(1,1))
            defenders=vcat(defenders,fill(0,1))
        elseif players[i,:Pos] == "D" || players[i,:Pos] == "LD" || players[i,:Pos] == "RD"
            wingers=vcat(wingers,fill(0,1))
            centers=vcat(centers,fill(0,1))
            defenders=vcat(defenders,fill(1,1))
        elseif players[i,:Pos] == "G"
            append!(goalie_indices, i)
            push!(goalies, [players[i, :Name],
                players[i, :Salary], players[i, :Team], players[i, :Opp],
                players[i, :Proj_FP]])
        else
            wingers=vcat(wingers,fill(0,1))
            centers=vcat(centers,fill(0,1))
            defenders=vcat(defenders,fill(1,1))
        end
    end

    deleterows!(players, goalie_indices)

    num_goalies = size(goalies)[1]

    num_players = size(players)[1]

    # Create team indicators from the information in the players file
    teams = unique(players[!, :Team])

    # Total number of teams
    num_teams = size(teams)[1]

    # player_info stores information on which team each player is on
    player_info = zeros(Int, num_teams)

    # Populate player_info with the corresponding information
    # Just doing the first skater so the rest can be in a loop
    for j=1:num_teams
        if players[1, :Team] == teams[j]
            player_info[j] = 1
            break
        end
    end
    players_teams = player_info'


    for i=2:num_players
        player_info = zeros(Int, num_teams)
        for j=1:num_teams
            if players[i, :Team] == teams[j]
                player_info[j] = 1
                break
            end
        end
        players_teams = vcat(players_teams, player_info')
    end

    # Create goalie identifiers so you know who they are playing
    opponents = goalies[!, :Opp]
    goalie_opponents = []

    # First goalie
    for num = 1:size(teams)[1]
        if opponents[1] == teams[num]
            goalie_opponents = players_teams[:, num]
            break
        end
    end

    # Remaining goalies
    for num = 2:size(opponents)[1]
        for num_2 = 1:size(teams)[1]
            if opponents[num] == teams[num_2]
                goalie_opponents = hcat(goalie_opponents, players_teams[:,num_2])
                break
            end
        end
    end

    # Create line indicators so you know which players are on which lines
    L1_info = zeros(Int, num_players)
    L2_info = zeros(Int, num_players)
    L3_info = zeros(Int, num_players)
    L4_info = zeros(Int, num_players)

    # First team
    for num=1:size(players)[1]
        if players[!, :Team][num] == teams[1]
            if ismissing(players[!, :Line][num])
                continue
            elseif players[!, :Line][num] == "1" || players[!, :Line][num] == 1
                L1_info[num] = 1
            elseif players[!, :Line][num] == "2" || players[!, :Line][num] == 2
                L2_info[num] = 1
            elseif players[!, :Line][num] == "3" || players[!, :Line][num] == 3
                L3_info[num] = 1
            elseif players[!, :Line][num] == "4" || players[!, :Line][num] == 4
                L4_info[num] = 1
            end
        end
    end
    team_lines = hcat(L1_info, L2_info, L3_info, L4_info)

    # Remaining teams
    for num2 = 2:size(teams)[1]
        L1_info = zeros(Int, num_players)
        L2_info = zeros(Int, num_players)
        L3_info = zeros(Int, num_players)
        L4_info = zeros(Int, num_players)
        for num=1:size(players)[1]
            if players[!, :Team][num] == teams[num2]
                if ismissing(players[!, :Line][num])
                    continue
                elseif players[!, :Line][num] == "1" || players[!, :Line][num] == 1
                    L1_info[num] = 1
                elseif players[!, :Line][num] == "2" || players[!, :Line][num] == 2
                    L2_info[num] = 1
                elseif players[!, :Line][num] == "3" || players[!, :Line][num] == 3
                    L3_info[num] = 1
                elseif players[!, :Line][num] == "4" || players[!, :Line][num] == 4
                    L4_info[num] = 1
                end
            end
        end
        team_lines = hcat(team_lines, L1_info, L2_info, L3_info, L4_info)
    end
    num_lines = size(team_lines)[2]

    # Create power play indicators
    # From the paper:
    # This constraint makes sure that any defenseman that is chosen
    # for the lineup is also in the first power play line of some team.
    # (First power play lines score more points)

    # First team
    PP_info = zeros(Int, num_players)
    for num=1:size(players)[1]
        if players[!, :Team][num] == teams[1]
            if ismissing(players[!, :PP_Line][num])
                continue
            elseif players[!, :PP_Line][num] == "1" || players[!, :PP_Line][num] == 1
                PP_info[num] = 1
            end
        end
    end

    P1_info = PP_info

    # Remaining teams
    for num2=2:size(teams)[1]
        PP_info = zeros(Int, num_players)
        for num=1:size(players)[1]
            if players[!, :Team][num] == teams[num2]
                if ismissing(players[!, :PP_Line][num])
                    continue
                elseif players[!, :PP_Line][num] == "1" || players[!, :PP_Line][num] == 1
                    PP_info[num] = 1
                end
            end
        end
        P1_info = hcat(P1_info, PP_info)
    end

    # Lineups using formulation as the stacking type
    the_lineup = formulation(players, goalies, hcat(zeros(Int, num_players + num_goalies), zeros(Int, num_players + num_goalies)), num_overlap, num_players, num_goalies, centers, wingers, defenders, num_teams, players_teams, goalie_opponents, team_lines, num_lines, P1_info)
    the_lineup2 = formulation(players, goalies, hcat(the_lineup, zeros(Int, num_players + num_goalies)), num_overlap, num_players, num_goalies, centers, wingers, defenders, num_teams, players_teams, goalie_opponents, team_lines, num_lines, P1_info)
    tracer = hcat(the_lineup, the_lineup2)
    for i=1:(num_lineups-2)
        try
            thelineup=formulation(players, goalies, tracer, num_overlap, num_players, num_goalies, centers, wingers, defenders, num_teams, players_teams, goalie_opponents, team_lines, num_lines, P1_info)
            tracer = hcat(tracer,thelineup)
        catch
            break
        end
    end


    # Create the output csv file
    lineup2 = ""
    for j = 1:size(tracer)[2]
        lineup = ["" "" "" "" "" "" "" "" ""]
        for i =1:num_players
            if tracer[i,j] == 1
                if centers[i]==1
                    if lineup[1]==""
                        lineup[1] = string(players[i,1])
                    elseif lineup[2]==""
                        lineup[2] = string(players[i,1])
                    elseif lineup[9] ==""
                        lineup[9] = string(players[i,1])
                    end
                elseif wingers[i] == 1
                    if lineup[3] == ""
                        lineup[3] = string(players[i,1])
                    elseif lineup[4] == ""
                        lineup[4] = string(players[i,1])
                    elseif lineup[5] == ""
                        lineup[5] = string(players[i,1])
                    elseif lineup[9] == ""
                        lineup[9] = string(players[i,1])
                    end
                elseif defenders[i]==1
                    if lineup[6] == ""
                        lineup[6] = string(players[i,1])
                    elseif lineup[7] ==""
                        lineup[7] = string(players[i,1])
                    elseif lineup[9] == ""
                        lineup[9] = string(players[i,1])
                    end
                end
            end
        end
        for i =1:num_goalies
            if tracer[num_players+i,j] == 1
                lineup[8] = string(goalies[i,1])
            end
        end
        for name in lineup
            lineup2 = string(lineup2, name, ",")
        end
        lineup2 = chop(lineup2)
        lineup2 = string(lineup2, """

        """)
    end
    println("Putting result in $(path_to_output)")
    outfile = open(path_to_output, "w")
    write(outfile, lineup2)
    close(outfile)
end

# Running the code
create_lineups(num_lineups, num_overlap, path_players, formulation, path_to_output)
print("Found $(num_lineups) lineups with a maximum overlap of $(num_overlap) in $(time() - start) seconds")
