import pandas as pd
import os
import csv
import glob

from common import backtest
from nba.src import nba_mip

league = 'nba'
strategies = ['MinOwn']
num_lineups = 20


def calculate_payout(payout_places, payout_date):
    payoff = 0
    payout_df = pd.read_csv('../results/%s/Payout.csv' % payout_date)
    for place in payout_places:
        index = payout_df['Minimum Place'].to_numpy().searchsorted(place, 'right')
        payoff += payout_df.iloc[index]['Payout']
    return round(payoff, 2)


def generate_backtest_data(backtest_strategy, backtest_date):
    for lineup_overlap_value in range(3, 8):
        backtest_path = '../strategies/%s/%s/' \
                        % (backtest_strategy, backtest_date)
        projections_path = '../results/%s/' % backtest_date
        nba_mip.generate_classic_lineups(backtest_date, projections_path, backtest_path, backtest_strategy,
                                         num_lineups, lineup_overlap_value)


def run_backtests():
    for strategy in strategies:
        for date_dir in os.listdir('../results'):
            payout_structure_path = '../results/%s/Payout.csv' % date_dir
            if not os.path.exists(payout_structure_path):
                print('Skipping %s' % date_dir)
                continue

            strategy_path = '../strategies/%s' % strategy
            if not os.path.isdir(strategy_path):
                os.mkdir(strategy_path)

            date_path = '%s/%s' % (strategy_path, date_dir)
            if not os.path.isdir(date_path):
                os.mkdir(date_path)

            generate_backtest_data(strategy, date_dir)
            payouts_path = '%s/Payout.csv' % date_path
            with open(payouts_path, 'w+', newline='') as payouts_file:
                csv_writer = csv.writer(payouts_file)
                csv_writer.writerow(['Overlap', 'Payout'])
                for overlap in range(3, 8):
                    lineup_path = '../../nba/strategies/%s/%s/%s lineups overlap %d.csv' \
                                  % (strategy, date_dir, date_dir, overlap)
                    glob_result = glob.glob('../results/%s/contest-standings-*.csv' % date_dir)
                    if len(glob_result) > 1:
                        raise Exception('More than one standings file found.')
                    elif len(glob_result) == 0:
                        raise Exception('Could not find standings file.')

                    results_path = '../nba/%s' % glob_result[0]
                    calculated_places = backtest.calculate_places(league, lineup_path, results_path)
                    payout = calculate_payout(calculated_places, date_dir)
                    csv_writer.writerow([overlap, payout])


def calculate_cumulative_stats():
    for strategy in strategies:
        strategy_path = '../strategies/%s' % strategy
        with open('%s/Results.csv' % strategy_path, 'w+', newline='') as results_file:
            csv_writer = csv.writer(results_file)
            csv_writer.writerow(['Date', 'Lineup Overlap', 'Payout'])
            for date_dir in os.listdir(strategy_path):
                if not date_dir.startswith('20'):
                    continue
                payouts_path = '%s/%s/Payout.csv' % (strategy_path, date_dir)
                with open(payouts_path) as payouts_file:
                    csv_reader = csv.reader(payouts_file)
                    for row in csv_reader:
                        if row[0] == 'Overlap':
                            continue
                        csv_writer.writerow([date_dir, row[0], row[1]])
