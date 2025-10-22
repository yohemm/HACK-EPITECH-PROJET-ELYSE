"""
Script de test pour vérifier le chargement des données CSV et les types
"""

import sys
sys.path.insert(0, '/Users/kevinbiantuadi/Downloads/my_projects/epitech_projects/piscine')

from app.utils.api_client import APIClient
import pandas as pd

print("=== Test chargement données couverture vaccinale ===\n")

# Tester fetch_coverage_vaccinale
df_coverage = APIClient.fetch_coverage_vaccinale()
print(f"Lignes chargées: {len(df_coverage)}")
print(f"Colonnes: {list(df_coverage.columns)}")
print(f"\nTypes de données:")
print(df_coverage.dtypes)
print(f"\nPremières lignes:")
print(df_coverage.head(10))
print(f"\nStatistiques coverage_rate:")
print(df_coverage['coverage_rate'].describe())

print("\n\n=== Test chargement données démographiques ===\n")

# Tester fetch_demographie_insee
df_demo = APIClient.fetch_demographie_insee()
print(f"Régions chargées: {len(df_demo)}")
print(f"Colonnes: {list(df_demo.columns)}")
print(f"\nTypes de données:")
print(df_demo.dtypes)
print(f"\nDonnées:")
print(df_demo)

print("\n\n=== Test données urgences (mock) ===\n")

# Tester fetch_urgences
df_urgences = APIClient.fetch_urgences()
print(f"Lignes chargées: {len(df_urgences)}")
print(f"Colonnes: {list(df_urgences.columns)}")
print(f"\nTypes de données:")
print(df_urgences.dtypes)
print(f"\nPremières lignes:")
print(df_urgences.head())

print("\n\n=== Vérification compatibilité merge ===\n")
print(f"Type 'code' dans coverage: {df_coverage['code'].dtype}")
print(f"Type 'code' dans urgences: {df_urgences['code'].dtype}")
print(f"Type 'code' dans demo: {df_demo['code'].dtype}")

# Test de merge
print("\nTest merge coverage + urgences:")
try:
    merged = pd.merge(df_coverage, df_urgences, on=['code', 'date'], how='outer')
    print(f"✓ Merge réussi! {len(merged)} lignes")
except Exception as e:
    print(f"✗ Erreur merge: {e}")

print("\n\nTest terminé avec succès!")
