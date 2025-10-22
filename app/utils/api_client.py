"""
Client pour fetch APIs data.gouv.fr
"""

import requests
import pandas as pd
import numpy as np
from typing import Dict
import streamlit as st

from app.config import API_URLS


class APIClient:
    """Fetch simplifié des APIs publiques"""
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def fetch_coverage_vaccinale() -> pd.DataFrame:
        """
        Récupère couverture vaccinale régionale depuis CSV local
        
        Returns:
            DataFrame avec code, date, coverage_rate, actes, doses
        """
        try:
            # Essayer de charger le CSV local
            import os
            csv_path = 'Couverture 2021-2024.csv'
            if os.path.exists(csv_path):
                return APIClient._load_coverage_from_csv(csv_path)
            
            # Sinon, essayer l'API
            response = requests.get(
                API_URLS['coverage'],
                params={'rows': 10000},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            records = [r['fields'] for r in data['records']]
            
            df = pd.DataFrame(records)
            df = df.rename(columns={
                'dept': 'code',
                'annee': 'date',
                'tx_couv_grippe': 'coverage_rate'
            })
            
            return df[['code', 'date', 'coverage_rate']]
        
        except Exception as e:
            st.warning(f"API couverture indisponible, utilisation donnees mock: {e}")
            return APIClient._mock_coverage_data()
    
    
    @staticmethod
    def _load_coverage_from_csv(csv_path: str) -> pd.DataFrame:
        """
        Charge et transforme le CSV de couverture vaccinale
        
        Structure CSV: region, code, variable, groupe, valeur, annee
        - variable: ACTE(VGP) ou DOSES(J07E1)
        - groupe: "65 ans et plus" ou "moins de 65 ans"
        
        Returns:
            DataFrame avec code, date, coverage_rate
        """
        df = pd.read_csv(csv_path)
        
        # Convertir 'code' en string dès le départ pour éviter les problèmes de merge
        df['code'] = df['code'].astype(str)
        
        # Pivoter pour avoir ACTE et DOSES en colonnes
        df_pivot = df.pivot_table(
            index=['code', 'annee', 'groupe'],
            columns='variable',
            values='valeur',
            aggfunc='sum'
        ).reset_index()
        
        # Calculer taux de couverture = ACTE / DOSES * 100 (pour milliers)
        # Les valeurs sont en "pour 1000 personnes", donc on multiplie par 100 pour avoir un %
        df_pivot['coverage_rate'] = (df_pivot['ACTE(VGP)'] / df_pivot['DOSES(J07E1)']) * 100
        
        # Renommer colonnes
        df_pivot = df_pivot.rename(columns={'annee': 'date'})
        
        # Convertir date en format YYYY-MM-DD (utiliser 01-01 par défaut)
        df_pivot['date'] = df_pivot['date'].astype(str) + '-01-01'
        
        # Garder colonnes utiles
        result = df_pivot[['code', 'date', 'coverage_rate', 'groupe']].copy()
        
        # Calculer moyenne pondérée si plusieurs groupes
        result_agg = result.groupby(['code', 'date'], as_index=False).agg({
            'coverage_rate': 'mean'
        })
        
        # S'assurer que 'code' est bien une string
        result_agg['code'] = result_agg['code'].astype(str)
        
        return result_agg
    
    
    @staticmethod
    def _mock_coverage_data() -> pd.DataFrame:
        """Donnees mock couverture pour tests (basees sur moyennes CSV)"""
        codes = ['11', '24', '27', '28', '32', '44', '52', '53', '75', '76', '84', '93', '94']
        dates = pd.date_range('2021-01-01', '2024-01-01', freq='YE')
        
        # Valeurs moyennes observées dans le CSV réel
        coverage_by_region = {
            '11': 72.3, '24': 63.6, '27': 56.6, '28': 65.7, '32': 51.8,
            '44': 59.8, '52': 62.2, '53': 61.5, '75': 58.0, '76': 60.4,
            '84': 57.0, '93': 57.1, '94': 34.4
        }
        
        data = []
        for code in codes:
            base_coverage = coverage_by_region.get(code, 60.0)
            for date in dates:
                # Variation annuelle légère
                coverage = base_coverage + np.random.uniform(-3, 3)
                data.append({
                    'code': code,
                    'date': date.strftime('%Y-%m-%d'),
                    'coverage_rate': max(0, min(100, coverage))
                })
        
        return pd.DataFrame(data)
    
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def fetch_urgences() -> pd.DataFrame:
        """
        Passages aux urgences grippe
        
        Returns:
            DataFrame avec code, date, urgences_count
        """
        try:
            response = requests.get(
                API_URLS['urgences'],
                params={'rows': 10000},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            records = [r['fields'] for r in data['records']]
            
            df = pd.DataFrame(records)
            # Adaptation selon structure réelle API
            df = df.rename(columns={
                'dept': 'code',
                'date': 'date',
                'sos_med_corona_urg': 'urgences_count'
            })
            
            return df[['code', 'date', 'urgences_count']]
        
        except Exception as e:
            # Fallback: données mock pour POC
            st.warning(f"API urgences indisponible, utilisation données mock: {e}")
            return APIClient._mock_urgences_data()
    
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def fetch_demographie_insee() -> pd.DataFrame:
        """
        Données démographiques complètes pour toutes les régions
        
        Returns:
            DataFrame avec code, name, population, density, pct_65plus
        """
        demo_data = {
            # Régions métropolitaines
            '11': {'name': 'Ile-de-France', 'population': 12278210, 'density': 1021, 'pct_65plus': 15.8},
            '24': {'name': 'Centre-Val de Loire', 'population': 2559073, 'density': 66, 'pct_65plus': 20.9},
            '27': {'name': 'Bourgogne-Franche-Comte', 'population': 2783039, 'density': 59, 'pct_65plus': 21.5},
            '28': {'name': 'Normandie', 'population': 3325032, 'density': 111, 'pct_65plus': 20.7},
            '32': {'name': 'Hauts-de-France', 'population': 5997734, 'density': 189, 'pct_65plus': 18.2},
            '44': {'name': 'Grand Est', 'population': 5511747, 'density': 97, 'pct_65plus': 19.4},
            '52': {'name': 'Pays de la Loire', 'population': 3832120, 'density': 119, 'pct_65plus': 19.2},
            '53': {'name': 'Bretagne', 'population': 3373835, 'density': 124, 'pct_65plus': 20.4},
            '75': {'name': 'Nouvelle-Aquitaine', 'population': 6033952, 'density': 72, 'pct_65plus': 21.8},
            '76': {'name': 'Occitanie', 'population': 5973969, 'density': 83, 'pct_65plus': 20.5},
            '84': {'name': 'Auvergne-Rhone-Alpes', 'population': 8078652, 'density': 116, 'pct_65plus': 19.1},
            '93': {'name': 'Provence-Alpes-Cote d\'Azur', 'population': 5081101, 'density': 161, 'pct_65plus': 20.8},
            '94': {'name': 'Corse', 'population': 343701, 'density': 40, 'pct_65plus': 23.7},
            # DOM (estimations)
            '01': {'name': 'Guadeloupe', 'population': 384239, 'density': 236, 'pct_65plus': 18.5},
            '02': {'name': 'Martinique', 'population': 364508, 'density': 326, 'pct_65plus': 22.1},
            '03': {'name': 'Guyane', 'population': 290691, 'density': 3, 'pct_65plus': 9.2},
            '04': {'name': 'La Reunion', 'population': 859959, 'density': 343, 'pct_65plus': 13.8},
            '06': {'name': 'Mayotte', 'population': 279471, 'density': 743, 'pct_65plus': 4.2},
        }
        
        rows = []
        for code, info in demo_data.items():
            rows.append({
                'code': code,
                'name': info['name'],
                'population': info['population'],
                'density': info['density'],
                'pct_65plus': info['pct_65plus']
            })
        
        return pd.DataFrame(rows)
    # ==================== MOCK DATA (POC) ====================
    
    @staticmethod
    def _mock_urgences_data() -> pd.DataFrame:
        """Donnees mock urgences pour tests"""
        codes = ['11', '24', '27', '28', '32', '44', '52', '53', '75', '76', '84', '93', '94']
        dates = pd.date_range('2021-01-01', '2024-01-01', freq='YE')
        
        # Proportionnel à la population
        urgences_factor = {
            '11': 1500, '24': 350, '27': 380, '28': 450, '32': 800,
            '44': 750, '52': 520, '53': 460, '75': 820, '76': 810,
            '84': 1100, '93': 690, '94': 50
        }
        
        data = []
        for code in codes:
            base_urgences = urgences_factor.get(code, 500)
            for date in dates:
                data.append({
                    'code': code,
                    'date': date.strftime('%Y-%m-%d'),
                    'urgences_count': int(base_urgences + np.random.randint(-100, 100))
                })
        
        return pd.DataFrame(data)
