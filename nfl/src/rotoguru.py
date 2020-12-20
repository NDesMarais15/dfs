from bs4 import BeautifulSoup
import urllib.request
import pandas as pd


def collect_players(week, year):
    fp = urllib.request.urlopen(
        'http://rotoguru1.com/cgi-bin/fyday.pl?week=%d&game=dk&scsv=1&year=%d' % (week, year))
    my_bytes = fp.read()

    my_str = my_bytes.decode('utf8')
    fp.close()
    sundays = pd.read_csv('../Helper Data/Sundays.csv')
    date = sundays[str(year)].iloc[week - 1]

    soup = BeautifulSoup(my_str, 'html.parser')
    for pre in soup.find_all('pre'):
        if pre.string is None:
            continue
        text_file = open('Historical Data/' + date + ' actual.scsv', '+w')
        text_file.write(pre.string)
        text_file.close()
