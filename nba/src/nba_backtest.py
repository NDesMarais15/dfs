import pandas as pd
import os
import csv
import glob

from common import backtest
from nba.src import nba_mip

league = 'nba'
strategies = ['MinTeam&100']
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
        backtest_strategy_components = backtest_strategy.split('&')
        nba_mip.generate_classic_lineups(backtest_date, projections_path, backtest_path,
                                         num_lineups, int(backtest_strategy_components[1]),
                                         lineup_overlap_value)


def run_backtests():
    for strategy in strategies:
        for date_dir in os.listdir('../results'):
            # generate_backtest_data(strategy, date_dir)
            payouts_path = '../strategies/%s/%s/Payout.csv' % (strategy, date_dir)
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
