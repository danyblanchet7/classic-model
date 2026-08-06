import pandas as pd

path = "C:/Users/danyblanchet7/Tips_and_tricks/Parameter_Confidence_Table.md"

#lecture files
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Garder seulement les lignes contenant des tableaux Markdown
table_lines = [
    line for line in lines
    if line.strip().startswith("|")
]

with open("temp_table.md", "w", encoding="utf-8") as f:
    f.writelines(table_lines)

df = pd.read_table(
    "temp_table.md",
    sep="|",
    engine="python"
)

# Nettoyage
df = df.iloc[:,1:-1]
df.columns = df.columns.str.strip()
df = df.apply(lambda x: x.str.strip())

df.to_csv(
    "C:/Users/danyblanchet7/Tips_and_tricks/Parameter_Confidence_Table.csv",
    index=False
)

print(df)