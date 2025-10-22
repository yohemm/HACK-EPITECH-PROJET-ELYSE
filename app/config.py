"""
Configuration globale du POC
"""

# URLs des APIs (data.gouv.fr)
API_URLS = {
    'coverage': 'https://odisse.santepubliquefrance.fr/api/records/1.0/search/?dataset=couvertures-vaccinales-des-adolescent-et-adultes-departement',
    'urgences': 'https://odisse.santepubliquefrance.fr/api/records/1.0/search/?dataset=grippe-passages-aux-urgences-et-actes-sos-medecins-departement',
    'ias': 'https://www.data.gouv.fr/api/1/datasets/indicateur-avance-sanitaire-ias-r-vaccination-grippe',
    'demo_insee': 'https://api.insee.fr/...'  # À adapter
}

# Poids pour le score composite
SCORING_WEIGHTS = {
    'coverage': 0.35,
    'urgences': 0.30,
    'density': 0.20,
    'age': 0.15
}

# Seuils
THRESHOLDS = {
    'coverage_target': 75.0,  # Objectif OMS
    'high_density': 500,       # Hab/km²
    'vulnerable_age': 65       # Âge
}

# Style carte
MAP_CONFIG = {
    'center_lat': 46.603354,
    'center_lon': 2.449389,
    'zoom': 5,
    'color_scale': ['#2ecc71', '#f39c12', '#e74c3c', '#8b0000']  # Vert → Rouge
}