import common.rotowire as rw
import datetime


def classic_today(slate):
    rw.collect_players('NHL', '', datetime.date.today(), slate)


classic_today('all')
