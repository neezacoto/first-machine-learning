# -*- coding: utf-8 -*-
"""BostonWeatherCS105Proj.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1FSKFC0YI2cny6x4JFKbdojefszei1lW5
"""

# put all my imports up here
from tqdm      import tqdm  # makes a progress bar
import sqlite3 as sql       # python sql library
import pandas  as pd        # manipulating tabular data
import numpy   as np        # linear algebra
import csv                  # read/write to .csv files in python
from sklearn.model_selection import train_test_split # test train split
from sklearn.ensemble import RandomForestRegressor # meta estimator that fits a number of classifying decision trees
from sklearn.inspection import PartialDependenceDisplay
from sklearn.inspection import plot_partial_dependence

# load the boston_weather_clean.csv into a DataFrame
weatherDfX: pd.DataFrame = pd.read_csv('boston_weather_clean.csv')

#maps the events into numbers
def map_event(x):
    dict = {
        "None": 0,
        "Rain": 0,
        "Snow": 1,
        "Both": 1
    }
    return dict[x]

#These collumns were decided to be left out as they have to do nothing with calculating snow or is bloat and the avg is sufficient enough
#weatherDf.drop([
# 'High Temp (F)', 
# 'Low Temp (F)',
# 'High Dew Point (F)',
# 'Low Dew Point (F)',
# 'Low Sea Level Press (in)',
# 'High Visibility (mi)',
# 'Avg Visibility (mi)',
# 'Low Visibility (mi)',
# 'Snowfall (in)'
# ], axis=1)

#first getting the events column then uses the map function to turn the strings into numeric values. This will be our ground truth Y
weatherDfY = weatherDfX.Events.map(map_event)

#VVVVVVVVVVVVVV IMPORTANT VVVVVVVVVVVVVVVVVVVVVVVV

#this is where all the other columns are dropped. This will be our X
# these were kept out for logistical reason, if someone can determine the features for this that would be great
weatherDfX.drop(weatherDfX.columns[[3,5,6,8,9,11,12,13,14,15,16,17,18,20,21,23]], axis=1, inplace=True)

# creates the weather database
weatherDb: object = sql.connect("weather_database.db")

# open a cursor to this database
cursor: object = weatherDb.cursor()

# creates the weather table in the database for X
cursor.execute('CREATE TABLE IF NOT EXISTS weatherX (Year number, Month number, AvgTemp number, AvgDewPoint number, AvgHumidity number, AvgWind number, Precip float)')
weatherDb.commit()
# creates the weather table in the database for Y
cursor.execute('CREATE TABLE IF NOT EXISTS weatherY  (Events number)')
weatherDb.commit()

# inputs the weather dataframe of X into the database
weatherDfX.to_sql('weatherX', weatherDb, if_exists='replace', index = False)
# inputs the weather dataframe of Y into the database
weatherDfY.to_sql('weatherY', weatherDb, if_exists='replace', index = False)

# Getting our X & Y
#-------------------------------
# selects all X
X = cursor.execute("""
SELECT *
FROM weatherX
""")

# Prints all rows
# for row in X.fetchall():
#   print (row)
#--------------------------------

#Turning the SQL back into CSV
#Turning X to csv
Xdf = pd.DataFrame(X)
#Xdf.to_csv (r'./weatherX.csv', index = False)
#how many columns
print(Xdf.shape[0])
chunks = np.array_split(Xdf.index, Xdf.shape[0])

for chunck, subset in enumerate(tqdm(chunks)):
    if chunck == 0: # first row
        Xdf.loc[subset].to_csv('./weatherX.csv', mode='w', index=True)
    else:
        Xdf.loc[subset].to_csv('./weatherX.csv', header=None, mode='a', index=True)

# selects all Y
Y = cursor.execute("""
SELECT *
FROM weatherY
""")

# Prints all rows
# for row in Y.fetchall():
#   print (row)
#-------------------------------
#Turning Y to csv
Ydf = pd.DataFrame(Y)
#Ydf.to_csv (r'./weatherY.csv', index = False)
print(Ydf.shape[0])
chunks = np.array_split(Ydf.index, Ydf.shape[0])

for chunck, subset in enumerate(tqdm(chunks)):
    if chunck == 0: # first row
        Ydf.loc[subset].to_csv('./weatherY.csv', mode='w', index=True)
    else:
        Ydf.loc[subset].to_csv('./weatherY.csv', header=None, mode='a', index=True)

#Now
#One is the X (Feature Matrix) and the other is the Y (Ground Truth)
#Then turn those into arrays that are usable by this train_test_split model
#docs: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html

#Reading the data we just cleaned up through
wX: pd.DataFrame = pd.read_csv('weatherX.csv')
#artifact column too lazy to fix so we'll just instead just name it and delete it
wX.set_axis(["bruh","Year", "Month", "Day","AvgTemp","AvgDewPoint","AvgHumidity","AvgWind","Precip"],
                    axis=1,inplace=True)
del wX["bruh"]

wy: pd.DataFrame = pd.read_csv('weatherY.csv')
wy.set_axis(["bruh","Event"],
                    axis=1,inplace=True)
del wy["bruh"]
#getting our test train split
X_train, X_test, y_train, y_test = train_test_split( wX, wy, test_size=0.33, random_state=42)

print("X_train \n", X_train)
print("y_train \n", y_train)
print("X_test \n", X_test)
print("y_test \n", y_test)

features = ["Month","AvgTemp", "AvgDewPoint", "AvgHumidity", "AvgWind","Precip"]
est = RandomForestRegressor(n_estimators=10)
# docs https://scikit-learn.org/stable/auto_examples/release_highlights/plot_release_highlights_0_24_0.html#sphx-glr-auto-examples-release-highlights-plot-release-highlights-0-24-0-py
# X = wX.to_numpy()
# y = wy.to_numpy()

est.fit(X_train, y_train)
display = plot_partial_dependence(
    est,
    X_train,
    features,
    kind="individual",
    subsample=50,
    n_jobs=3,
    grid_resolution=20,
    random_state=0,
)
display.figure_.suptitle(
    "Partial dependence of Events on weather features\n"
    "for determining snow or rain"
)
display.figure_.subplots_adjust(hspace=0.5)

from sklearn import tree # decision tree
from matplotlib import pyplot as plt # shows the plot
from google.colab import files

# docs https://scikit-learn.org/stable/modules/generated/sklearn.tree.plot_tree.html

# creating our decision tree
clf = tree.DecisionTreeClassifier(max_leaf_nodes=50, random_state=0)

clf = clf.fit(X_train, y_train)
fig, axe = plt.subplots(figsize=(100,50))
artists = tree.plot_tree(decision_tree=clf, filled=True, rounded=True, fontsize=16, max_depth=30)
plt.savefig('dectree.jpg',dpi=150)
#files.download("dectree.jpg")
plt.show()

from sklearn.tree import DecisionTreeRegressor
import matplotlib.pyplot as plt
# attempting to do this 
# https://scikit-learn.org/stable/auto_examples/tree/plot_tree_regression.html?highlight=decision
# well this isn't working
# Fit regression model
regr_1 = DecisionTreeRegressor(max_depth=5)
regr_2 = DecisionTreeRegressor(max_depth=10)
regr_1.fit(X_train, y_train)
regr_2.fit(X_train, y_train)

# Predict
y_1 = regr_1.predict(X_test)
y_2 = regr_2.predict(X_test)
print(X_train.index)
print(y_train.index)

# Converting Dataframes 2d structure into 1d arrays, I think
Xt=np.arange(0,len(X_train),1)
yt=np.arange(0,len(y_train),1)

# Plot the results
plt.figure()
plt.scatter(Xt, yt, s=100, edgecolor="black", c="darkorange", label="data")
plt.plot(X_test, y_1, color="cornflowerblue", label="max_depth=2", linewidth=2)
plt.plot(X_test, y_2, color="yellowgreen", label="max_depth=5", linewidth=2)
plt.xlabel("data")
plt.ylabel("target")
plt.title("Decision Tree Regression")
plt.legend()
plt.show()
