import pandas as pd

df = pd.read_json("data/records.json")

print("Rows and columns:", df.shape)
print(df.head())

print("\nRules per stage:")
print(df["stage"].value_counts())

print("\nRules per applies_to:")
print(df["applies_to"].value_counts())

print("\nRules per source document:")
print(df["source_doc"].value_counts())

df["rule_length"] = df["rule"].str.len()
print("\nRule length:")
print(df["rule_length"].describe())