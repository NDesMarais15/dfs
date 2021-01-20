from xgboost import XGBRegressor
import pandas as pd
from racing_reference_constants import *
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
import numpy as np

label_encoder = LabelEncoder()
one_hot_encoder = OneHotEncoder(sparse=False, categories='auto')


def one_hot_encode(column):
    feature = label_encoder.fit_transform(racing_data[column])
    feature = feature.reshape(racing_data.shape[0], 1)
    return one_hot_encoder.fit_transform(feature)


def label_encode(column):
    return label_encoder.fit_transform(racing_data[column])


def rolling_average(column):
    for driver in racing_data[DRIVER].unique():
        driver_df = racing_data.loc[(racing_data[DRIVER] == driver)]
        for n in [20]:
            for i in range(0, n):
                if len(driver_df.index) == i:
                    break
                racing_data.at[driver_df.iloc[i].name, column + ' Rolling Average Last ' + str(n)] = 0
            for i in range(n, len(driver_df.index)):
                racing_data.at[driver_df.iloc[i].name, column + ' Rolling Average Last ' + str(n)] = \
                    driver_df.iloc[i - n:i][column].mean()
        for track in racing_data[TRACK_NAME].unique():
            driver_df = racing_data.loc[(racing_data[DRIVER] == driver) & (racing_data[TRACK_NAME] == track)]
            for n in [3]:
                for i in range(0, n):
                    if len(driver_df.index) == i:
                        break
                    racing_data.at[driver_df.iloc[i].name, column + ' Rolling Track Average Last ' + str(n)] = 0
                for i in range(n, len(driver_df.index)):
                    racing_data.at[driver_df.iloc[i].name, column + ' Rolling Track Average Last ' + str(n)] = \
                        driver_df.iloc[i - n:i][column].mean()


racing_data = pd.read_csv('../data/racing_reference2.csv', encoding='latin1', parse_dates=['Date'])
kfold = KFold(n_splits=2)

racing_data = racing_data.sort_values(DATE)

# rolling_average(FANTASY_POINTS)
# rolling_average(QUALITY_PASSES)
# rolling_average(PASS_DIFF)
# rolling_average(DRIVER_RATING)
# racing_data = racing_data.loc[racing_data['Fantasy Points Rolling Track Average Last 3'] != 0]
# racing_data = racing_data.loc[racing_data['Fantasy Points Rolling Average Last 20'] != 0]
# racing_data = racing_data.loc[racing_data['Driver Rating Rolling Track Average Last 3'] != 0]

track_feature = one_hot_encode(TRACK_NAME)
driver_feature = one_hot_encode(DRIVER)
# brand_feature = encode(CAR_BRAND)
# racing_data['TRACK_LABELS'] = track_feature
# racing_data['DRIVER_LABELS'] = driver_feature
# racing_data['BRAND_LABELS'] = brand_feature
# racing_data['RAND'] = np.random.randint(1, 100000, racing_data.shape[0])

y = racing_data[FANTASY_POINTS]
racing_data = racing_data.drop([RACE, DATE, TRACK_NAME, LAPS, TRACK_LENGTH, FINISHING_POSITION, DRIVER, CAR_BRAND,
                                LAPS_LED, QUALIFYING_RANK, QUALIFYING_SPEED, QUALIFYING_TIME, PRACTICE_RANK,
                                PRACTICE_SPEED, PRACTICE_TIME, PASS_DIFF, QUALITY_PASSES, DRIVER_RATING,
                                FASTEST_LAPS, FANTASY_POINTS,
                                AVERAGE_FANTASY_POINTS, AVERAGE_FANTASY_POINTS_FOR_TRACK], axis=1)

for j in range(1, np.size(track_feature, 1)):
    racing_data['TRACK_' + str(j)] = track_feature[:, j]

for j in range(0, np.size(driver_feature, 1)):
    racing_data['DRIVER_' + str(j)] = driver_feature[:, j]

for col in racing_data.columns:
    print(col)

model = XGBRegressor()
for train_index, test_index in kfold.split(racing_data, y):
    cv_train, cv_test = racing_data.iloc[train_index], racing_data.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]
    model.fit(cv_train, y_train)
    y_pred = model.predict(cv_test)
    mse = mean_squared_error(y_pred, y_test, squared=False)
    print(mse)
    # print(y_pred)
    print(model.feature_importances_)

# race_feature = race_feature.reshape()
