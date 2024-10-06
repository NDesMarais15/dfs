import datetime
import pandas as pd
import nfl_mip
import nfl_backtest
from common import daily_fantasy_fuel, rotoguru

num_lineups = 25
lineup_overlap = 4
league = 'nfl'


def collect_historical_projections():
    sundays = pd.read_csv('../helper/Sundays.csv')
    for year in range(2016, 2021):
        for date in sundays[str(year)]:
            daily_fantasy_fuel.collect_players(league, date, '../historical/')


def classic_today(strategy):
    daily_fantasy_fuel.collect_players(league, datetime.date.today(), '')
    nfl_mip.generate_classic_lineups(datetime.date.today(), '', '', num_lineups, lineup_overlap, strategy)


def showdown_today(strategy):
    daily_fantasy_fuel.collect_players(league, datetime.date.today(), '')
    nfl_mip.generate_showdown_lineups(datetime.date.today(), '', '', num_lineups, lineup_overlap, strategy)


def run_date(date, strategy, slate=None):
    daily_fantasy_fuel.collect_players(league, date, '', slate)
    nfl_mip.generate_classic_lineups(date, '', '', num_lineups, lineup_overlap, strategy)


def run_showdown_date(date, strategy):
    daily_fantasy_fuel.collect_players(league, date, '')
    nfl_mip.generate_showdown_lineups(date, '', '', num_lineups, lineup_overlap, strategy)


def generate_historical_lineup(date, strategy):
    nfl_mip.generate_classic_lineups(date, 'historical/', '', num_lineups, lineup_overlap, strategy)


def generate_past_contest_lineup(date, strategy):
    daily_fantasy_fuel.collect_players(league, date, '')
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


run_date('2024-10-06', '1R+NoRB&RB+NoPlayervsDef', '1BF00')

