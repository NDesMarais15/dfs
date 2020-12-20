import datetime
import pandas as pd
import mip
import rotogrinders
import rotoguru

num_lineups = 3
lineup_overlap = 5


def collect_historical_projections():
    sundays = pd.read_csv('../Helper Data/Sundays.csv')
    for year in range(2016, 2021):
        for date in sundays[str(year)]:
            rotogrinders.collect_players(date, 'Historical Data/', -1)


def classic_today(strategy, slate_id):
    rotogrinders.collect_players(datetime.date.today(), '', slate_id)
    mip.generate_classic_lineups(datetime.date.today(), '', '', num_lineups, lineup_overlap, strategy)


def showdown_today(strategy, slate_id):
    rotogrinders.collect_players(datetime.date.today(), '', slate_id)
    mip.generate_showdown_lineups(datetime.date.today(), '', '', num_lineups, lineup_overlap, strategy)


def run_date(date, strategy, slate_id):
    rotogrinders.collect_players(date, '', slate_id)
    mip.generate_classic_lineups(date, '', '', num_lineups, lineup_overlap, strategy)


def run_showdown_date(date, strategy, slate_id):
    rotogrinders.collect_players(date, '', slate_id)
    mip.generate_showdown_lineups(date, '', '', num_lineups, lineup_overlap, strategy)


def generate_historical_lineup(date, strategy):
    mip.generate_classic_lineups(date, 'Historical Data/', '', num_lineups, lineup_overlap, strategy)


def generate_past_contest_lineup(date, strategy, slate_id):
    rotogrinders.collect_players(date, '', slate_id)
    mip.generate_classic_lineups(date, '', 'Strategies/%s/%s/' % (strategy, date),
                                 num_lineups, lineup_overlap, strategy)


def collect_historical_results():
    for year in range(2016, 2021):
        for week in range(1, 18):
            rotoguru.collect_players(week, year)


def collect_historical_data():
    collect_historical_projections()
    collect_historical_results()


showdown_today('2R+1OppR+NoRB&RB+NoQBvsDef', 42637)
