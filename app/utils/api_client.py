"""
Client pour fetch APIs data.gouv.fr
"""

import requests
import pandas as pd
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
        response = requests.get(
            API_URLS['coverage'],
            params={'rows': 10000}
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
    
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def fetch_urgences() -> pd.DataFrame:
        """Passages aux urgences grippe"""
        # Même pattern que coverage
        response = requests.get(API_URLS['urgences'], params={'rows': 10000})
        # ... traitement similaire
        return df[['code', 'date', 'urgences_count']]
    
    
    @staticmethod
    @st.cache_data(ttl=86400)  # 24h (données demo statiques)
    def fetch_demographie_insee() -> pd.DataFrame:
        """Données démographiques INSEE"""
        # Fetch population, densité, structure âge
        # ... (peut être CSV statique si API complexe)
        return df[['code', 'name', 'population', 'density', 'pct_65plus']]