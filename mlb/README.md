Fantasy Baseball Lineups Optimization Code
======================

This code builds off of the source code here:
https://github.com/zlisto/Daily-Fantasy-Baseball-Contests-in-DraftKings


This is a rewritten version which fixes some of the errors that now occur in the original code due to
updates in Julia and other dependencies in this code. Additionally, there is a python script for 
collecting players from RotoGrinders.

You can find information about running the Julia parts of the repo in the link above. 
In order to run the Python script, simply use `python collect_players.py`. You can add which teams
you want to collect players for into the `teams.py` file. There is also a file in this repo with a
list of the accepted team abbreviations and which MLB team they map to.

I tried to use this strategy on DraftKings in August 2019 with mostly bad results. There is data on
my performance, as well as the lineups that were used in the contests, in the "Results" folder of this
repository.
