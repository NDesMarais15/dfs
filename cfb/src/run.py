from src.rotowire import collect_players
from src.mip import *
from src.backtest import *


num_lineups = 5
lineup_overlap = 5

# collect_players('../', '12/5', 'All')
generate_classic_lineups('2020-12-05', '../', num_lineups, lineup_overlap, 'NoRB&RB+2QB+1WR')
calculate_places('../2020-12-05 lineups overlap %d.csv' % lineup_overlap,
                 '../Results/2020-12-05/Slate 1/contest-standings-97844084.csv')
