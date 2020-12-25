import datetime
from common import rotogrinders
import mip

league = 'nba'
num_lineups = 3
lineup_overlap = 4


def showdown_today(slate_id):
    rotogrinders.collect_players(league, datetime.date.today(), '', slate_id)


def classic_today():
    rotogrinders.collect_players(league, datetime.date.today(), '', -1)
    mip.generate_classic_lineups(datetime.date.today(), '', '', num_lineups, lineup_overlap)


def run_date(date):
    rotogrinders.collect_players(league, date, '', -1)
    mip.generate_classic_lineups(date, '', '', num_lineups, lineup_overlap)


classic_today()
