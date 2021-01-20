import json
import os
import csv
import datetime

with open('../data/proj.csv', 'w+', newline='', encoding='utf-8') as proj_csv:
    csv_writer = csv.writer(proj_csv, delimiter=',', quotechar='"')
    csv_writer.writerow(['Date', 'Name', 'Projected Fantasy Points', 'Salary'])
    for file in os.listdir('../Data'):
        with open("../Data/" + file, 'r') as file_reader:
            rg_json = json.loads(file_reader.read())
            date = datetime.datetime.strptime(file[:-5], '%Y-%m-%d')
            date = date + datetime.timedelta(days=1)

            for player in rg_json['players']['generic_player']:
                player_entry = rg_json['players']['generic_player'][player]
                name = player_entry['player']['first_name'] + ' ' + player_entry['player']['last_name']
                fpts = player_entry['fpts']['20']
                salary = player_entry['schedule']['salaries'][0]['import_id'][0]['salary']
                csv_writer.writerow([date.date(), name, fpts, salary])
