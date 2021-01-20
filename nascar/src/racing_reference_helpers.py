from bs4 import BeautifulSoup
import urllib.request
from racing_reference_constants import *


def get_html_string(url):
    url_info = urllib.request.urlopen(url)
    url_bytes = url_info.read()
    url_info.close()
    return url_bytes.decode('utf8')


def get_qualifying_results(qualifier_url):
    soup = BeautifulSoup(get_html_string(BASE_RACING_REFERENCE_URL + qualifier_url), 'html.parser')
    qualifying_data = {}
    for table in soup.find_all('table'):
        if QUALIFYING_RESULTS_TABLE_IDENTIFIER in table.getText():
            for row in table.find_all('tr', {'class': ['odd', 'even']}):
                cells = row.find_all('td')
                player_name = cells[1].find('a').getText()
                qualifying_data[player_name] = {}
                qualifying_data[player_name][QUALIFYING_RANK] = cells[0].get_text()
                qualifying_data[player_name][QUALIFYING_TIME] = cells[4].get_text()
                qualifying_data[player_name][QUALIFYING_SPEED] = cells[5].get_text()
    return qualifying_data


def get_loop_data(loop_data_url):
    soup = BeautifulSoup(get_html_string(BASE_RACING_REFERENCE_URL + loop_data_url), 'html.parser')
    loop_data = {}
    for table in soup.find_all('table'):
        if LOOP_DATA_TABLE_IDENTIFIER in table.getText():
            for row in table.find_all('tr', {'class': ['odd', 'even']}):
                cells = row.find_all('td')
                player_name = cells[0].find('a').getText()
                loop_data[player_name] = {}
                loop_data[player_name][PASS_DIFF] = cells[7].get_text()
                loop_data[player_name][QUALITY_PASSES] = cells[10].get_text()
                loop_data[player_name][FASTEST_LAPS] = cells[12].get_text()
                loop_data[player_name][DRIVER_RATING] = cells[18].get_text()
    return loop_data


def get_practice_data(loop_data_url):
    soup = BeautifulSoup(get_html_string(BASE_RACING_REFERENCE_URL + loop_data_url), 'html.parser')
    practice_data = {}
    for table in soup.find_all('table'):
        if PRACTICE_DATA_TABLE_IDENTIFIER in table.getText():
            for row in table.find_all('tr', {'class': ['odd', 'even']}):
                cells = row.find_all('td')
                player_name = cells[1].find('a').getText()
                practice_data[player_name] = {}
                practice_data[player_name][PRACTICE_RANK] = cells[0].get_text()
                practice_data[player_name][PRACTICE_TIME] = cells[4].get_text()
                practice_data[player_name][PRACTICE_SPEED] = cells[6].get_text()
    return practice_data
