from urllib.error import URLError

from bs4 import BeautifulSoup
import urllib.request
import pandas as pd


# This appears at the end of the header for the NBA scsv's
scsv_nba_line_end_indicator = 'Stat line\n'


def collect_nfl_players(week, year):
    fp = urllib.request.urlopen(
        'http://rotoguru1.com/cgi-bin/fyday.pl?week=%d&game=dk&scsv=1&year=%d' % (week, year))
    my_bytes = fp.read()

    my_str = my_bytes.decode('utf8')
    fp.close()
    sundays = pd.read_csv('../nfl/helper/Sundays.csv')
    date = sundays[str(year)].iloc[week - 1]

    soup = BeautifulSoup(my_str, 'html.parser')
    for pre in soup.find_all('pre'):
        if pre.string is None:
            continue
        text_file = open('../nfl/historical/' + date + ' actual.scsv', '+w')
        text_file.write(pre.string)
        text_file.close()


def collect_nba_players(year, month, day):
    url = 'http://rotoguru1.com/cgi-bin/hyday.pl?scsv=1&game=dk&year=%d&mon=%d&day=%d' % (year, month, day)
    try:
        fp = urllib.request.urlopen(url)
    except URLError as e:
        print('Failed to connect to %s because of the following error: %s' % (url, e))
        return

    my_str = fp.read()

    fp.close()

    soup = BeautifulSoup(my_str, 'html.parser')
    for pre in soup.find_all('pre'):
        if pre.string is None or pre.string.endswith(scsv_nba_line_end_indicator):
            continue
        text_file = open('../../nba/historical/%d-%02d-%02d actual.scsv' % (year, month, day), '+w')
        text_file.write(pre.string)
        text_file.close()
        print('%d-%02d-%02d is complete' % (year, month, day))



