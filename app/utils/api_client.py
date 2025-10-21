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
        Récupère couverture vaccinale départementale
        
        Returns:
            DataFrame avec code, date, coverage_rate
        """
        try:
            response = requests.get(
                API_URLS['coverage'],
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
                'annee': 'date',
                'tx_couv_grippe': 'coverage_rate'
            })
            
            return df[['code', 'date', 'coverage_rate']]
        
        except Exception as e:
            # Fallback: données mock pour POC
            st.warning(f"API couverture indisponible, utilisation données mock: {e}")
            return APIClient._mock_coverage_data()
    
    
    @staticmethod
    def _mock_coverage_data() -> pd.DataFrame:
        """Données mock couverture pour tests"""
        import numpy as np
        
        codes = ['75', '13', '69', '31', '06', '44', '33', '59', '67', '34',
                 '92', '93', '94', '78', '77', '91', '35', '38', '62', '76']
        dates = pd.date_range('2024-01-01', '2024-10-01', freq='W')
        
        data = []
        for code in codes:
            # Base coverage entre 40-80% avec variation
            base_coverage = np.random.uniform(45, 75)
            for date in dates:
                # Variation hebdomadaire
                coverage = base_coverage + np.random.uniform(-5, 5)
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
    @st.cache_data(ttl=86400)  # 24h (données demo statiques)
    def fetch_demographie_insee() -> pd.DataFrame:
        """
        Données démographiques INSEE
        
        Returns:
            DataFrame avec code, name, population, density, pct_65plus
        """
        # Pour le POC, utiliser données statiques
        # En production: API INSEE ou CSV officiel
        return APIClient._mock_demo_data()
    
    
    # ==================== MOCK DATA (POC) ====================
    
    @staticmethod
    def _mock_urgences_data() -> pd.DataFrame:
        """Données mock urgences pour tests"""
        import numpy as np
        
        codes = ['75', '13', '69', '31', '06', '44', '33', '59', '67', '34']
        dates = pd.date_range('2024-01-01', '2024-10-01', freq='W')
        
        data = []
        for code in codes:
            for date in dates:
                data.append({
                    'code': code,
                    'date': date.strftime('%Y-%m-%d'),
                    'urgences_count': np.random.randint(50, 500)
                })
        
        return pd.DataFrame(data)
    
    
    @staticmethod
    def _mock_demo_data() -> pd.DataFrame:
        """Données démographiques mock"""
        demo_data = {
            '75': {'name': 'Paris', 'population': 2175601, 'density': 20754, 'pct_65plus': 14.5},
            '13': {'name': 'Bouches-du-Rhône', 'population': 2043110, 'density': 393, 'pct_65plus': 18.2},
            '69': {'name': 'Rhône', 'population': 1872808, 'density': 557, 'pct_65plus': 16.1},
            '31': {'name': 'Haute-Garonne', 'population': 1415757, 'density': 223, 'pct_65plus': 15.3},
            '06': {'name': 'Alpes-Maritimes', 'population': 1094283, 'density': 254, 'pct_65plus': 22.7},
            '44': {'name': 'Loire-Atlantique', 'population': 1442686, 'density': 209, 'pct_65plus': 17.1},
            '33': {'name': 'Gironde', 'population': 1647269, 'density': 165, 'pct_65plus': 18.5},
            '59': {'name': 'Nord', 'population': 2608346, 'density': 459, 'pct_65plus': 16.8},
            '67': {'name': 'Bas-Rhin', 'population': 1142258, 'density': 240, 'pct_65plus': 17.2},
            '34': {'name': 'Hérault', 'population': 1175623, 'density': 191, 'pct_65plus': 19.3},
            '92': {'name': 'Hauts-de-Seine', 'population': 1624357, 'density': 9188, 'pct_65plus': 15.2},
            '93': {'name': 'Seine-Saint-Denis', 'population': 1644518, 'density': 6989, 'pct_65plus': 12.8},
            '94': {'name': 'Val-de-Marne', 'population': 1410865, 'density': 5675, 'pct_65plus': 16.4},
            '78': {'name': 'Yvelines', 'population': 1448207, 'density': 656, 'pct_65plus': 17.9},
            '77': {'name': 'Seine-et-Marne', 'population': 1421197, 'density': 242, 'pct_65plus': 15.6},
            '91': {'name': 'Essonne', 'population': 1321617, 'density': 733, 'pct_65plus': 15.1},
            '35': {'name': 'Ille-et-Vilaine', 'population': 1096356, 'density': 163, 'pct_65plus': 16.7},
            '38': {'name': 'Isère', 'population': 1271166, 'density': 161, 'pct_65plus': 17.4},
            '62': {'name': 'Pas-de-Calais', 'population': 1472589, 'density': 220, 'pct_65plus': 18.1},
            '76': {'name': 'Seine-Maritime', 'population': 1262808, 'density': 203, 'pct_65plus': 19.2},
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