import datetime
import pandas as pd
import nfl_mip
import nfl_backtest
from common import rotogrinders, rotoguru

num_lineups = 33
lineup_overlap = 4
league = 'nfl'


def collect_historical_projections():
    sundays = pd.read_csv('../helper/Sundays.csv')
    for year in range(2016, 2021):
        for date in sundays[str(year)]:
            rotogrinders.collect_players(league, date, '../historical/', -1)


def classic_today(strategy, slate_id):
    rotogrinders.collect_players(league, datetime.date.today(), '', slate_id)
    nfl_mip.generate_classic_lineups(datetime.date.today(), '', '', num_lineups, lineup_overlap, strategy)


def showdown_today(strategy, slate_id):
    rotogrinders.collect_players(league, datetime.date.today(), '', slate_id)
    nfl_mip.generate_showdown_lineups(datetime.date.today(), '', '', num_lineups, lineup_overlap, strategy)


def run_date(date, strategy, slate_id):
    rotogrinders.collect_players(league, date, '', slate_id)
    nfl_mip.generate_classic_lineups(date, '', '', num_lineups, lineup_overlap, strategy)


def run_showdown_date(date, strategy, slate_id):
    rotogrinders.collect_players(league, date, '', slate_id)
    nfl_mip.generate_showdown_lineups(date, '', '', num_lineups, lineup_overlap, strategy)


def generate_historical_lineup(date, strategy):
    nfl_mip.generate_classic_lineups(date, 'historical/', '', num_lineups, lineup_overlap, strategy)


def generate_past_contest_lineup(date, strategy, slate_id):
    rotogrinders.collect_players(league, date, '', slate_id)
    nfl_mip.generate_classic_lineups(date, '', '../strategies/%s/%s/' % (strategy, date),
                                     num_lineups, lineup_overlap, strategy)


def collect_historical_results():
    for year in range(2016, 2021):
        for week in range(1, 18):
            rotoguru.collect_nfl_players(week, year)


def collect_historical_data():
    collect_historical_projections()
    collect_historical_results()


def run_backtests():
    nfl_backtest.run_backtests()


showdown_today('2R+1OppR+NoRB&RB+NoQBvsDef', 44059)
