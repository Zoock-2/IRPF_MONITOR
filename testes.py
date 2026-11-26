import pandas as pd
from config import ARQ_PLANILHA_FINAL, CSV

df_original = pd.read_excel(ARQ_PLANILHA_FINAL, dtype=str)
df_original["Data Transmissão"] = df_original["Data Transmissão"].fillna("").str.strip()
print(df_original["Data Transmissão"].dtype)

