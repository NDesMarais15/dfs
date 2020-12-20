# This code solves for multiple baseball lineups

include("data_cleaning.jl")
include("baseball_formulations.jl")  #this code has all the different formualations


################################################################################################################
################################################################################################################
################################################################################################################
function find_lineups()
    #INPUT PARAMS
    # num_lineups is the total number of lineups
    num_lineups = 20;

    # num_overlap is the maximum overlap of players between the lineups
    num_overlap = 6;

    #number of hitters in the stack (number of consecutive hitters in the hitting order)
    stack_size = 5;

    #FORMULATION:  formulation is the type of formulation that you would like to use.
    formulation = baseball_formulation

    #path to the csv file with the players information (pitchers and hitters);
    path_pitchers = "2019-08-09 pitchers.csv"
    path_hitters = "2019-08-09 hitters.csv"

    # path_to_output is a string  that gives the path to the csv file that will give the outputted results
    path_to_output= string(string(formulation), "_stacksize_", stack_size,"_overlap_", num_overlap,"_lineups_", num_lineups,".csv");

    # path_to_output_proj is a string  that gives the path to the csv file that will give the outputted results with projected lineup points
    path_to_output_proj = string("proj_baseball_", string(formulation), "_stacksize_", stack_size,"_overlap_", num_overlap,"_lineups_", num_lineups,".csv");

    # path_to_output_actual is a string  that gives the path to the csv file that will give the outputted results with projected and actual lineup points
    path_to_output_actual = string("actual_baseball_", string(formulation), "_stacksize_", stack_size,"_overlap_", num_overlap,"_lineups_", num_lineups,".csv");

    #########################################################################
    # Running the code
    println("Calculating DraftKings baseball linueps.\n ", num_lineups, " lineups\n","Formulation  ",formulation,
    "\nOverlap = ", num_overlap,"\nStack size = ", stack_size)

    create_lineups(num_lineups, num_overlap, stack_size,formulation, path_pitchers,path_hitters,  path_to_output);

    println("\nCalculated DraftKings baseball lineups.\n\tNumber of lineups = ", num_lineups, " \n\tStack size = ",stack_size,
    "\n\tOverlap = ", num_overlap,"\n" )

    println("Saving data to file ",path_to_output)

    #save the projected and actual points for the lineups
    lineup_points_proj(path_to_output,path_hitters,path_pitchers,path_to_output_proj);
    #lineup_points_actual(path_to_output,path_hitters,path_pitchers,path_to_output_actual);
end
find_lineups()
