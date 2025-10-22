"""
core/risk_analyzer.py - CLASSE PRINCIPALE (POC)
Fetch + Calcul + Simulation en une seule classe
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import streamlit as st

from app.utils.api_client import APIClient
from app.config import SCORING_WEIGHTS


class RiskAnalyzer:
    """
    Classe centrale du POC - Tout-en-un simplifié
    
    Responsabilités :
    1. Fetch données APIs → DataFrame unifié
    2. Calcul score de risque composite
    3. Simulation de scénarios
    4. Exports pour visualisation
    """
    
    def __init__(self):
        """Initialise avec cache Streamlit intégré"""
        self.api_client = APIClient()
        self._data: Optional[pd.DataFrame] = None
        self._scores: Optional[pd.DataFrame] = None
        self.last_update: Optional[datetime] = None
    
    
    # ==================== 1. FETCH DONNÉES ====================
    
    @st.cache_data(ttl=3600)  # Cache 1h
    def load_data(_self, date_start: str = "2024-01-01") -> pd.DataFrame:
        """
        Charge et fusionne TOUTES les données depuis APIs
        
        Returns:
            DataFrame unifié avec colonnes :
            - code (str) : Code INSEE département
            - name (str) : Nom département
            - date (str) : YYYY-MM-DD
            - coverage_rate (float) : Taux couverture (%)
            - urgences_count (int) : Passages urgences
            - population (int) : Population totale
            - density (float) : Hab/km²
            - pct_65plus (float) : % 65+ ans
        """
        # Fetch parallèle des 4 sources
        df_coverage = _self.api_client.fetch_coverage_vaccinale()
        df_urgences = _self.api_client.fetch_urgences()
        df_demo = _self.api_client.fetch_demographie_insee()
        
        # Extraire année pour merge (dates exactes différentes)
        df_coverage['year'] = pd.to_datetime(df_coverage['date']).dt.year
        df_urgences['year'] = pd.to_datetime(df_urgences['date']).dt.year
        
        # Fusion sur (code, year)
        data = pd.merge(df_coverage, df_urgences, on=['code', 'year'], how='inner', suffixes=('', '_urg'))
        data = pd.merge(data, df_demo, on='code', how='left')
        
        # Nettoyer colonnes doublons
        if 'date_urg' in data.columns:
            data = data.drop(columns=['date_urg'])
        
        # Nettoyage
        data = data.dropna(subset=['coverage_rate', 'urgences_count'])
        data['date'] = pd.to_datetime(data['date'])
        
        _self._data = data
        _self.last_update = datetime.now()
        
        return data
    
    
    # ==================== 2. CALCUL SCORES ====================
    
    def compute_risk_scores(self, data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Calcule le score de risque composite pour chaque territoire
        
        Formule : Score = Σ(weight_i × score_i)
        - score_coverage : Plus faible = plus risqué
        - score_urgences : Plus élevé = plus risqué
        - score_density : Plus dense = plus risqué
        - score_age : Plus de 65+ = plus risqué
        
        Returns:
            DataFrame avec colonnes score_* et risk_level
        """
        if data is None:
            data = self._data
        
        df = data.copy()
        
        # Normalisation des scores (0-100, 100 = risque max)
        df['score_coverage'] = self._normalize_coverage(df['coverage_rate'])
        df['score_urgences'] = self._normalize_urgences(df['urgences_count'])
        df['score_density'] = self._normalize_density(df['density'])
        df['score_age'] = self._normalize_age(df['pct_65plus'])
        
        # Score composite
        df['risk_score'] = (
            SCORING_WEIGHTS['coverage'] * df['score_coverage'] +
            SCORING_WEIGHTS['urgences'] * df['score_urgences'] +
            SCORING_WEIGHTS['density'] * df['score_density'] +
            SCORING_WEIGHTS['age'] * df['score_age']
        )
        
        # Catégorie de risque
        df['risk_level'] = pd.cut(
            df['risk_score'],
            bins=[0, 25, 50, 75, 100],
            labels=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        )
        
        self._scores = df
        return df
    
    
    # ---------- Méthodes de normalisation ----------
    
    @staticmethod
    def _normalize_coverage(coverage: pd.Series) -> pd.Series:
        """Plus la couverture est faible, plus le score est élevé"""
        # Formule : score = 100 - (coverage × k) avec seuil 75%
        return np.clip(100 - (coverage * 1.33), 0, 100)
    
    @staticmethod
    def _normalize_urgences(urgences: pd.Series) -> pd.Series:
        """Normalisation min-max sur les passages urgences"""
        # On compare à la médiane nationale
        median = urgences.median()
        ratio = urgences / median
        return np.clip(ratio * 50, 0, 100)
    
    @staticmethod
    def _normalize_density(density: pd.Series) -> pd.Series:
        """Densité normalisée : plus dense = score plus élevé"""
        # Log-scale pour densité (écarts importants entre rural/urbain)
        log_density = np.log1p(density)
        return (log_density / log_density.max()) * 100
    
    @staticmethod
    def _normalize_age(pct_65plus: pd.Series) -> pd.Series:
        """% 65+ normalisé : plus élevé = plus vulnérable"""
        return np.clip((pct_65plus / 30) * 100, 0, 100)  # 30% = max théorique
    
    
    # ==================== 3. REQUÊTES ====================
    
    def get_score_by_territory(
        self,
        code: str,
        date: Optional[str] = None
    ) -> Dict:
        """
        Obtient le score d'un territoire spécifique
        
        Returns:
            {
                'risk_score': 78.5,
                'risk_level': 'HIGH',
                'details': {
                    'coverage': 45.2,
                    'urgences': 1250,
                    'density': 5200,
                    'pct_65plus': 22.5
                },
                'scores_detail': {
                    'score_coverage': 65.0,
                    'score_urgences': 82.0,
                    ...
                }
            }
        """
        if self._scores is None:
            self.compute_risk_scores()
        
        # Dernière date si non spécifiée
        if date is None:
            date = self._scores['date'].max()
        
        row = self._scores[
            (self._scores['code'] == code) &
            (self._scores['date'] == date)
        ]
        
        if row.empty:
            raise ValueError(f"Territoire {code} introuvable pour date {date}")
        
        r = row.iloc[0]
        
        return {
            'code': code,
            'name': r['name'],
            'risk_score': round(r['risk_score'], 1),
            'risk_level': r['risk_level'],
            'details': {
                'coverage_rate': r['coverage_rate'],
                'urgences_count': int(r['urgences_count']),
                'population': int(r['population']),
                'density': round(r['density'], 1),
                'pct_65plus': round(r['pct_65plus'], 1)
            },
            'scores_detail': {
                'score_coverage': round(r['score_coverage'], 1),
                'score_urgences': round(r['score_urgences'], 1),
                'score_density': round(r['score_density'], 1),
                'score_age': round(r['score_age'], 1)
            }
        }
    
    
    def get_all_scores(
        self,
        date: Optional[str] = None,
        level: str = 'departmental'
    ) -> pd.DataFrame:
        """
        Retourne tous les scores pour une date (pour carte)
        """
        if self._scores is None:
            self.compute_risk_scores()
        
        if date is None:
            date = self._scores['date'].max()
        
        return self._scores[
            self._scores['date'] == date
        ][['code', 'name', 'risk_score', 'risk_level', 
           'coverage_rate', 'urgences_count']].copy()
    
    
    def get_top_risks(self, n: int = 10, date: Optional[str] = None) -> pd.DataFrame:
        """Top N territoires les plus à risque"""
        scores = self.get_all_scores(date)
        return scores.nlargest(n, 'risk_score')
    
    
    # ==================== 4. SIMULATION ====================
    
    def simulate_coverage_change(
        self,
        code: str,
        new_coverage: float,
        date: Optional[str] = None
    ) -> Dict:
        """
        Simule l'impact d'un changement de couverture
        
        Returns:
            {
                'current_score': 78.5,
                'new_score': 62.3,
                'delta': -16.2,
                'new_risk_level': 'MEDIUM'
            }
        """
        current = self.get_score_by_territory(code, date)
        
        # Nouveau score de couverture
        new_score_cov = self._normalize_coverage(pd.Series([new_coverage])).iloc[0]
        
        # Recalcul du score total
        old_score_cov = current['scores_detail']['score_coverage']
        delta_cov = (new_score_cov - old_score_cov) * SCORING_WEIGHTS['coverage']
        
        new_total = current['risk_score'] + delta_cov
        
        # Nouvelle catégorie
        new_level = pd.cut(
            [new_total],
            bins=[0, 25, 50, 75, 100],
            labels=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        )[0]
        
        return {
            'current_score': current['risk_score'],
            'current_coverage': current['details']['coverage_rate'],
            'new_score': round(new_total, 1),
            'new_coverage': new_coverage,
            'delta': round(delta_cov, 1),
            'new_risk_level': new_level
        }
    
    
    # ==================== 5. COMPARAISON ====================
    
    def compare_territories(
        self,
        codes: List[str],
        date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Compare plusieurs territoires
        
        Returns:
            DataFrame avec scores côte à côte
        """
        comparisons = []
        for code in codes:
            try:
                score_data = self.get_score_by_territory(code, date)
                comparisons.append({
                    'Code': code,
                    'Nom': score_data['name'],
                    'Score Risque': score_data['risk_score'],
                    'Niveau': score_data['risk_level'],
                    'Couverture (%)': score_data['details']['coverage_rate'],
                    'Urgences': score_data['details']['urgences_count'],
                    'Densité': score_data['details']['density']
                })
            except ValueError:
                continue
        
        return pd.DataFrame(comparisons)
    
    
    # ==================== 6. TIMELINE ====================
    
    def get_evolution(self, code: str) -> pd.DataFrame:
        """
        Évolution temporelle d'un territoire
        
        Returns:
            DataFrame avec date, risk_score, risk_level
        """
        if self._scores is None:
            self.compute_risk_scores()
        
        return self._scores[
            self._scores['code'] == code
        ][['date', 'risk_score', 'risk_level', 'coverage_rate']].sort_values('date')