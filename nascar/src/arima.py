from statsmodels.tsa.arima.model import ARIMA
import pandas as pd
from racing_reference_constants import *
from sklearn.metrics import mean_squared_error
from matplotlib import pyplot
from pandas.plotting import autocorrelation_plot
pyplot.show()

racing_data = pd.read_csv('../data/racing_reference2.csv', encoding='latin1', parse_dates=['Date'])
racing_data = racing_data.drop([RACE, LAPS, TRACK_LENGTH, FINISHING_POSITION, CAR_BRAND,
                                LAPS_LED, QUALIFYING_RANK, QUALIFYING_SPEED, QUALIFYING_TIME, PRACTICE_RANK,
                                PRACTICE_SPEED, PRACTICE_TIME, PASS_DIFF, QUALITY_PASSES, DRIVER_RATING,
                                FASTEST_LAPS, STARTING_POSITION, QUALIFYING_PRACTICE_RANK, AVERAGE_FANTASY_POINTS,
                                AVERAGE_FANTASY_POINTS_FOR_TRACK], axis=1)

drivers = racing_data[DRIVER].unique()
for driver in drivers:
    driver_data = racing_data[(racing_data[DRIVER] == driver)]
    driver_data = driver_data.drop([DRIVER, DATE, TRACK_NAME], axis=1)
    X = driver_data.values
    autocorrelation_plot(X)
    pyplot.show()
    print(X.std())
    size = int(len(X) * 0.66)
    train, test = X[0:size], X[size:len(X)]
    history = [x for x in train]
    predictions = list()
    if len(test) <= 5:
        continue
    for t in range(len(test)):
        model = ARIMA(history, order=(5, 1, 0))
        model_fit = model.fit()
        output = model_fit.forecast()
        y_hat = output[0]
        predictions.append(y_hat)
        obs = test[t]
        history.append(obs)
        # print('predicted=%f, expected=%f' % (y_hat, obs))
    error = mean_squared_error(test, predictions, squared=False)
    print('Test MSE: %.3f' % error)
    pyplot.plot(test)
    pyplot.plot(predictions, color='red')
    pyplot.title(driver)
    pyplot.show()
#
# for driver in drivers:
#     for track in tracks:
#         driver_data = racing_data[(racing_data[DRIVER] == driver) & (racing_data[TRACK_NAME] == track)]
#         driver_data = driver_data.drop([DRIVER, DATE, TRACK_NAME], axis=1)
#         X = driver_data.values
#         # autocorrelation_plot(X)
#         # pyplot.show()
#         size = int(len(X) * 0.66)
#         train, test = X[0:size], X[size:len(X)]
#         history = [x for x in train]
#         predictions = list()
#         if len(test) <= 4:
#             continue
#         for t in range(len(test)):
#             model = ARIMA(history, order=(3, 1, 0))
#             model_fit = model.fit()
#             output = model_fit.forecast()
#             y_hat = output[0]
#             predictions.append(y_hat)
#             obs = test[t]
#             history.append(obs)
#             # print('predicted=%f, expected=%f' % (y_hat, obs))
#         error = mean_squared_error(test, predictions, squared=False)
#         print('Test MSE: %.3f' % error)
#         pyplot.plot(test)
#         pyplot.plot(predictions, color='red')
#         pyplot.title(driver)
#         pyplot.show()
