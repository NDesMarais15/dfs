import datetime
from common import rotogrinders, rotoguru
import mip

league = 'nba'
num_lineups = 20
num_candidates = 100
lineup_overlap = 6


def showdown_today(slate_id):
    rotogrinders.collect_players(league, datetime.date.today(), '', slate_id)


def classic_today():
    rotogrinders.collect_players(league, datetime.date.today(), '', -1)
    mip.generate_classic_lineups(datetime.date.today(), '', '', num_lineups, num_candidates,
                                 lineup_overlap)


def run_date(date):
    rotogrinders.collect_players(league, date, '', -1)
    mip.generate_classic_lineups(date, '', '', num_lineups, num_candidates, lineup_overlap)


def collect_historical_results():
    # This is the first date of data on rotoguru for NBA
    date = datetime.date(2014, 10, 28)

    while date <= datetime.date.today():
        rotoguru.collect_nba_players(date.year, date.month, date.day)
        date += datetime.timedelta(days=1)


def collect_historical_projections():
    date = datetime.date(2017, 1, 16)

    while date <= datetime.date.today():
        rotogrinders.collect_players(league, date, '../Historical Data/', -1)
        date += datetime.timedelta(days=1)


classic_today()
