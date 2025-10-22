"""
Configuration globale du POC
"""

# URLs des APIs (data.gouv.fr)
API_URLS = {
    'coverage': 'https://odisse.santepubliquefrance.fr/api/records/1.0/search/?dataset=couvertures-vaccinales-des-adolescent-et-adultes-departement',
    'urgences': 'https://odisse.santepubliquefrance.fr/api/records/1.0/search/?dataset=grippe-passages-aux-urgences-et-actes-sos-medecins-departement',
    'ias': 'https://www.data.gouv.fr/api/1/datasets/indicateur-avance-sanitaire-ias-r-vaccination-grippe',
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

"""
Configuration de base pour le scoring composite
"""

# Poids par défaut pour le score composite
DEFAULT_SCORING_WEIGHTS = {
    'coverage': 0.35,    # Couverture vaccinale
    'urgences': 0.30,    # Passages aux urgences
    'density': 0.20,     # Densité de population
    'age': 0.15          # Structure d'âge (% 65+)
}

# Limites pour les curseurs de simulation
SIMULATION_LIMITS = {
    'coverage': {
        'min': 0.0,
        'max': 100.0,
        'default': 55.0,
        'step': 1.0,
        'unit': '%'
    },
    'urgences': {
        'min': 0,
        'max': 5000,
        'default': 500,
        'step': 50,
        'unit': 'passages'
    },
    'density': {
        'min': 10,
        'max': 20000,
        'default': 100,
        'step': 10,
        'unit': 'hab/km²'
    },
    'age_65plus': {
        'min': 0.0,
        'max': 40.0,
        'default': 20.0,
        'step': 0.5,
        'unit': '% 65+'
    }
}

# Seuils pour catégorisation du risque
RISK_CATEGORIES = {
    'LOW': (0, 25),
    'MEDIUM': (25, 50),
    'HIGH': (50, 75),
    'CRITICAL': (75, 100)
}

# Couleurs pour visualisation
RISK_COLORS = {
    'LOW': '#2ecc71',       # Vert
    'MEDIUM': '#f39c12',    # Orange
    'HIGH': '#e74c3c',      # Rouge
    'CRITICAL': '#8b0000'   # Rouge foncé
}