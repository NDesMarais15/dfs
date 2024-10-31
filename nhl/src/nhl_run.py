import common.daily_fantasy_fuel as dff
import nhl_mip
import datetime

num_lineups = 25
lineup_overlap = 5
league = 'nhl'


def classic_today(strategy):
    dff.collect_players('nhl', '2024-10-31', '')
    nhl_mip.generate_classic_lineups(datetime.date.today(), '', '', num_lineups, lineup_overlap, strategy)


classic_today('NoSkatervsG')
