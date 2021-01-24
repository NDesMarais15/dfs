import common.rotowire as rw
import datetime


def classic_today():
    rw.collect_players('NHL', '', datetime.date.today(), 'Early')


classic_today()
