from racing_reference_code import RacingReferenceCode
import logging
import csv
from racing_reference_helpers import *
import re
import time


logging.basicConfig(filename='racing_reference_scrape_logs.txt', filemode='w', level=logging.INFO)
start_time = time.time()
races_html_strings = []
for year in range(2010, 2021):
    year_url = BASE_RACES_URL + '?yr=' + str(year)
    races_html_strings.append(get_html_string(year_url))

race_urls = {}
race_dates = {}
for races_html_string in races_html_strings:
    soup = BeautifulSoup(races_html_string, 'html.parser')
    for table in soup.find_all('table'):
        if RACE_TABLE_IDENTIFIER in table.getText():
            for row in table.find_all('tr', TABLE_ROW_FILTER):
                cells = row.find_all('td')
                if NASCAR_IDENTIFIER in cells[3].getText():
                    link = cells[1].find('a')['href']
                    link_components = link.split('/')
                    if len(link_components) != 4:
                        logging.warning('Malformed link: ' + link)
                        continue
                    try:
                        if RacingReferenceCode.is_regular_season(link_components[3]):
                            race_urls[link_components[2]] = link
                            race_dates[link_components[2]] = cells[0].getText()
                    except Exception as e:
                        print(str(e) + ' for link ' + link)

with open(RACE_CSV, "w", newline='') as race_csv:
    csv_writer = csv.writer(race_csv)
    csv_writer.writerow([RACE,
                         DATE,
                         TRACK_NAME,
                         LAPS,
                         TRACK_LENGTH,
                         FINISHING_POSITION,
                         STARTING_POSITION,
                         DRIVER,
                         CAR_BRAND,
                         LAPS_LED,
                         QUALIFYING_RANK,
                         QUALIFYING_TIME,
                         QUALIFYING_SPEED,
                         PRACTICE_RANK,
                         PRACTICE_TIME,
                         PRACTICE_SPEED,
                         PASS_DIFF,
                         QUALITY_PASSES,
                         DRIVER_RATING,
                         FASTEST_LAPS])

    for race_name, race_url in race_urls.items():
        race_html_string = get_html_string(BASE_RACING_REFERENCE_URL + race_url)
        soup = BeautifulSoup(race_html_string, 'html.parser')
        laps = 0
        track_length = 0
        track_name = ''

        practice_data = {}
        qualifying_data = {}
        loop_data = {}

        players_copied = False
        for table in soup.find_all('table'):
            if LAPS_IDENTIFIER in table.text:
                for a in table.find_all('a'):
                    if TRACK_LINK_IDENTIFIER in a['href']:
                        track_name = a.getText()
                track_description = re.search(TRACK_DESCRIPTION_REGEX, str(table))
                if track_description is None:
                    logging.warning(race_name + 'does not have a description.')
                    continue
                word_list = track_description.group(0).split()
                laps = word_list[0]
                track_length = float(word_list[4])

            elif LOOP_DATA_IDENTIFIER in table.text:
                for a in table.find_all('a'):
                    if QUALIFYING_LINK_RESULTS_IDENTIFIER in a.text:
                        qualifying_data = get_qualifying_results(a['href'])
                    elif LOOP_DATA_IDENTIFIER in a.text:
                        loop_data = get_loop_data(a['href'])
                    elif PRACTICE_DATA_IDENTIFIER in a.text:
                        practice_data = get_practice_data(a['href'])

            elif PLAYERS_TABLE_IDENTIFIER in str(table.text) and not players_copied:
                for tr in table.find_all('tr', TABLE_ROW_FILTER):
                    cells = tr.find_all('td')
                    if len(cells) != 11:
                        continue
                    finishing_pos = cells[0].get_text()
                    starting_pos = cells[1].get_text().strip()
                    if cells[3].find('a') is None:
                        break
                    driver_name = cells[3].find('a').get_text()
                    car_brand = cells[5].get_text()
                    laps_led = cells[9].get_text()

                    if qualifying_data == {}:
                        qualifying_place = -1
                        qualifying_time = -1
                        qualifying_speed = -1
                    else:
                        if driver_name not in qualifying_data:
                            qualifying_place = -1
                            qualifying_time = -1
                            qualifying_speed = -1
                            logging.warning('Driver ' + driver_name + ' not found in qualifying data')
                        else:
                            qualifying_place = qualifying_data[driver_name][QUALIFYING_RANK]
                            qualifying_time = qualifying_data[driver_name][QUALIFYING_TIME]
                            qualifying_speed = qualifying_data[driver_name][QUALIFYING_SPEED]

                    if practice_data == {}:
                        practice_rank = -1
                        practice_time = -1
                        practice_speed = -1
                    else:
                        if driver_name not in practice_data:
                            practice_rank = -1
                            practice_time = -1
                            practice_speed = -1
                            logging.warning('Driver ' + driver_name + ' not found in practice data')
                        else:
                            practice_rank = practice_data[driver_name][PRACTICE_RANK]
                            practice_time = practice_data[driver_name][PRACTICE_TIME]
                            practice_speed = practice_data[driver_name][PRACTICE_SPEED]

                    if loop_data == {}:
                        pass_diff = -1
                        quality_passes = -1
                        driver_rating = -1
                        fastest_laps = -1
                    else:
                        if driver_name not in loop_data:
                            pass_diff = -1
                            quality_passes = -1
                            driver_rating = -1
                            fastest_laps = -1
                            logging.warning('Driver ' + driver_name + ' not found in loop data')
                        else:
                            pass_diff = loop_data[driver_name][PASS_DIFF]
                            quality_passes = loop_data[driver_name][QUALITY_PASSES]
                            driver_rating = loop_data[driver_name][DRIVER_RATING]
                            fastest_laps = loop_data[driver_name][FASTEST_LAPS]

                    csv_writer.writerow([race_name,
                                         race_dates[race_name],
                                         track_name,
                                         laps,
                                         track_length,
                                         finishing_pos,
                                         starting_pos,
                                         driver_name,
                                         car_brand,
                                         laps_led,
                                         qualifying_place,
                                         qualifying_time,
                                         qualifying_speed,
                                         practice_rank,
                                         practice_time,
                                         practice_speed,
                                         pass_diff,
                                         quality_passes,
                                         driver_rating,
                                         fastest_laps])
                players_copied = True

end_time = time.time()
logging.info('Script ran in ' + str(end_time - start_time) + ' seconds.')
