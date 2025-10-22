"""
Script debug pour vérifier les données après load_data et compute_risk_scores
"""

import sys
sys.path.insert(0, '/Users/kevinbiantuadi/Downloads/my_projects/epitech_projects/piscine')

from app.utils.api_client import APIClient
import pandas as pd

print("=" * 60)
print("=== Debug étape par étape ===")
print("=" * 60)

print("\n1. Chargement couverture...")
df_coverage = APIClient.fetch_coverage_vaccinale()
print(f"Coverage: {len(df_coverage)} lignes")
print(f"Codes: {sorted(df_coverage['code'].unique())}")
print(f"Dates: {sorted(df_coverage['date'].unique())}")

print("\n2. Chargement urgences...")
df_urgences = APIClient.fetch_urgences()
print(f"Urgences: {len(df_urgences)} lignes")
print(f"Codes: {sorted(df_urgences['code'].unique())}")
print(f"Dates: {sorted(df_urgences['date'].unique())}")

print("\n3. Chargement démographie...")
df_demo = APIClient.fetch_demographie_insee()
print(f"Demo: {len(df_demo)} lignes")
print(f"Codes: {sorted(df_demo['code'].unique())}")

print("\n4. Ajout colonne year...")
df_coverage['year'] = pd.to_datetime(df_coverage['date']).dt.year
df_urgences['year'] = pd.to_datetime(df_urgences['date']).dt.year
print(f"Coverage years: {sorted(df_coverage['year'].unique())}")
print(f"Urgences years: {sorted(df_urgences['year'].unique())}")

print("\n5. Premier merge (coverage + urgences sur year)...")
data = pd.merge(df_coverage, df_urgences, on=['code', 'year'], how='inner', suffixes=('', '_urg'))
print(f"Après merge 1: {len(data)} lignes")
print(f"Codes: {sorted(data['code'].unique())}")
print(f"\nPremières lignes:")
print(data.head())
print(f"\nNaN dans coverage_rate: {data['coverage_rate'].isna().sum()}")
print(f"NaN dans urgences_count: {data['urgences_count'].isna().sum()}")

print("\n6. Deuxième merge (+ démographie)...")
data = pd.merge(data, df_demo, on='code', how='left')
print(f"Après merge 2: {len(data)} lignes")
print(f"\nPremières lignes:")
print(data.head())

print("\n7. Après dropna...")
data_clean = data.dropna(subset=['coverage_rate', 'urgences_count'])
print(f"Après dropna: {len(data_clean)} lignes")
print(f"Codes restants: {sorted(data_clean['code'].unique()) if len(data_clean) > 0 else 'Aucun'}")

print("\n" + "=" * 60)
print("✓ Debug terminé!")
print("=" * 60)
