from common.rotowire import collect_players
from mip import *
from backtest import *


num_lineups = 5
lineup_overlap = 5

collect_players('CFB', '../', '2020-12-05', 'All')
generate_classic_lineups('2020-12-05', '../', num_lineups, lineup_overlap, 'NoRB&RB+2QB+1WR')
calculate_places('../2020-12-05 lineups overlap %d.csv' % lineup_overlap,
                 '../results/2020-12-05/Slate 2/contest-standings-97844084.csv')
