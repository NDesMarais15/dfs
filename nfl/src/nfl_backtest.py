import pandas as pd
import csv

from common import backtest
from nfl.src import nfl_mip

league = 'nfl'
strategies = ['2R+1OppR+NoPlayervsDef+NoRB&RB', '2R+1OppR+NoQBvsDef+NoRB&RB']
entry_dates = ['2020-11-13', '2020-11-19', '2021-01-09', '2021-01-10']
slates = [1, 1, 2, 3]
weeks = [10, 11, 18, 18]
contest_ids = {'2020-11-13': '96410219', '2020-11-19': '96813915',
               '2021-01-09': '100391197', '2021-01-10': '100509179'}
num_lineups = 20


def calculate_payout(payout_places, payout_week, payout_slate):
    payoff = 0
    payout_df = pd.read_csv('../results/Week %d/Classic/Slate %d/Payout.csv' % (payout_week, payout_slate))
    for place in payout_places:
        index = payout_df['Minimum Place'].to_numpy().searchsorted(place, 'right')
        payoff += payout_df.iloc[index - 1]['Payout']
    return round(payoff, 2)


def generate_backtest_data(backtest_date, backtest_week, backtest_slate, backtest_strategy, slate_id):
    for lineup_overlap_value in range(2, 8):
        backtest_path = '../strategies/%s/Week %d/Classic/Slate %d/' \
                        % (backtest_strategy, backtest_week, backtest_slate)
        projections_path = '../results/Week %d/Classic/Slate %d/' % (backtest_week, backtest_slate)
        nfl_mip.generate_classic_lineups(backtest_date, projections_path, backtest_path,
                                         num_lineups, lineup_overlap_value, backtest_strategy)


def write_teams(week_to_write, slate_to_write):
    with open('../../common/rg_teams.py', 'w+') as teams:
        with open('../results/Week %d/Classic/Slate %d/teams.py' % (week_to_write, slate_to_write)) as old_teams:
            teams.write(old_teams.read())


def run_backtests():
    for strategy in strategies:
        for i in range(0, 4):
            entry_date = entry_dates[i]
            week = weeks[i]
            slate = slates[i]
            write_teams(week, slate)
            generate_backtest_data(entry_date, week, slate, strategy, -1)
            payouts_path = '../strategies/%s/Week %d/Classic/Slate %d/Payout.csv' % (strategy, week, slate)
            with open(payouts_path, 'w+', newline='') as payouts_file:
                csv_writer = csv.writer(payouts_file)
                csv_writer.writerow(['Overlap', 'Payout'])
                for j in range(2, 8):
                    lineup_path = '../strategies/%s/Week %d/Classic/Slate %d/%s lineups overlap %d.csv' \
                                  % (strategy, week, slate, entry_date, j)
                    results_path = '../results/Week %d/Classic/Slate %d/contest-standings-%s.csv' \
                                   % (week, slate, contest_ids[entry_date])
                    calculated_places = backtest.calculate_places(league, lineup_path, results_path)
                    payout = calculate_payout(calculated_places, week, slate)
                    csv_writer.writerow([j, payout])
