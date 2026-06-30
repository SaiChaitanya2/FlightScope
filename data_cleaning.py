import pandas as pd

# Combine January and February data
df1 = pd.read_csv("Flights_2022_1.csv", low_memory=False)
df2 = pd.read_csv("Flights_2022_2.csv", low_memory=False)

df = pd.concat([df1, df2], ignore_index=True)

print(df.head())
print(df.shape)

print(df.isnull().sum())

#df.drop(['Year', 'Quarter'], axis=1, inplace=True)

# Drop columns that are completely null
df.dropna(axis=1, how='all', inplace=True)

print("After dropping null columns:")
print(df.shape)