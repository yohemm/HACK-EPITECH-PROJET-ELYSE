"""
RiskAnalyzer - Calcul du score composite et simulations
Focus sur : scoring configurable + simulation multi-paramètres
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

from config import DEFAULT_SCORING_WEIGHTS, RISK_CATEGORIES


@dataclass
class TerritoryMetrics:
    """Métriques d'un territoire pour calcul de score"""
    code: str
    name: str
    coverage_rate: float        # 0-100 %
    urgences_count: int          # Nombre de passages
    population_density: float    # hab/km²
    pct_65plus: float           # 0-100 %


@dataclass
class RiskScore:
    """Résultat du calcul de score"""
    total: float                 # Score composite 0-100
    coverage_score: float        # Score normalisé couverture
    urgences_score: float        # Score normalisé urgences
    density_score: float         # Score normalisé densité
    age_score: float            # Score normalisé âge
    risk_level: str             # LOW, MEDIUM, HIGH, CRITICAL
    weights_used: Dict[str, float]  # Poids appliqués


class RiskAnalyzer:
    """
    Classe pour calcul de score composite et simulations
    
    Formule du score :
    Score = w_cov × S_cov + w_urg × S_urg + w_den × S_den + w_age × S_age
    
    Où chaque S_* est normalisé entre 0-100 (100 = risque max)
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialise l'analyseur
        
        Args:
            weights: Poids personnalisés (sinon utilise DEFAULT_SCORING_WEIGHTS)
        """
        self.weights = weights or DEFAULT_SCORING_WEIGHTS.copy()
        self._validate_weights()
    
    
    def _validate_weights(self) -> None:
        """Vérifie que les poids somment à 1.0"""
        total = sum(self.weights.values())
        if not 0.99 <= total <= 1.01:  # Tolérance pour float
            raise ValueError(f"Les poids doivent sommer à 1.0 (actuel: {total})")
    
    
    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """
        Met à jour les poids de scoring
        
        Args:
            new_weights: Nouveaux poids {'coverage': 0.4, ...}
        """
        self.weights.update(new_weights)
        self._validate_weights()
    
    
    # ==================== NORMALISATION DES SCORES ====================
    
    @staticmethod
    def normalize_coverage(coverage_rate: float) -> float:
        """
        Normalise le taux de couverture vaccinale
        
        Logique : Plus la couverture est FAIBLE, plus le score est ÉLEVÉ
        - 100% couverture → score 0 (risque nul)
        - 0% couverture → score 100 (risque max)
        
        Formule : score = 100 - coverage_rate
        """
        return np.clip(100.0 - coverage_rate, 0, 100)
    
    
    @staticmethod
    def normalize_urgences(
        urgences_count: int,
        baseline: int = 500,
        max_expected: int = 5000
    ) -> float:
        """
        Normalise les passages aux urgences
        
        Logique : Plus de passages = risque plus élevé
        
        Args:
            urgences_count: Nombre de passages
            baseline: Valeur de référence (médiane nationale)
            max_expected: Valeur maximale attendue
        
        Formule : score = (urgences / max) × 100
        """
        ratio = urgences_count / max_expected
        return np.clip(ratio * 100, 0, 100)
    
    
    @staticmethod
    def normalize_density(
        population_density: float,
        rural_threshold: float = 50,
        urban_threshold: float = 2000
    ) -> float:
        """
        Normalise la densité de population
        
        Logique : Plus dense = propagation plus rapide = risque élevé
        Utilise échelle logarithmique car grandes variations (10 à 20000 hab/km²)
        
        Args:
            population_density: Hab/km²
            rural_threshold: Seuil rural (score min)
            urban_threshold: Seuil urbain (score max)
        
        Formule : score = log_normalize(density)
        """
        if population_density <= rural_threshold:
            return 0.0
        elif population_density >= urban_threshold:
            return 100.0
        else:
            # Normalisation logarithmique entre seuils
            log_density = np.log10(population_density)
            log_rural = np.log10(rural_threshold)
            log_urban = np.log10(urban_threshold)
            
            normalized = (log_density - log_rural) / (log_urban - log_rural)
            return np.clip(normalized * 100, 0, 100)
    
    
    @staticmethod
    def normalize_age(pct_65plus: float, vulnerability_threshold: float = 25.0) -> float:
        """
        Normalise la structure d'âge (% 65+)
        
        Logique : Plus de personnes âgées = plus vulnérable = risque élevé
        
        Args:
            pct_65plus: Pourcentage de 65+ ans
            vulnerability_threshold: Seuil de vulnérabilité élevée
        
        Formule : score = (pct_65plus / threshold) × 100
        """
        ratio = pct_65plus / vulnerability_threshold
        return np.clip(ratio * 100, 0, 100)
    
    
    # ==================== CALCUL SCORE COMPOSITE ====================
    
    def compute_risk_score(self, metrics: TerritoryMetrics) -> RiskScore:
        """
        Calcule le score de risque composite pour un territoire
        
        Args:
            metrics: Métriques du territoire
        
        Returns:
            RiskScore avec score total et détails
        """
        # Calcul des scores normalisés individuels
        score_coverage = self.normalize_coverage(metrics.coverage_rate)
        score_urgences = self.normalize_urgences(metrics.urgences_count)
        score_density = self.normalize_density(metrics.population_density)
        score_age = self.normalize_age(metrics.pct_65plus)
        
        # Score composite pondéré
        total_score = (
            self.weights['coverage'] * score_coverage +
            self.weights['urgences'] * score_urgences +
            self.weights['density'] * score_density +
            self.weights['age'] * score_age
        )
        
        # Catégorisation du risque
        risk_level = self._categorize_risk(total_score)
        
        return RiskScore(
            total=round(total_score, 1),
            coverage_score=round(score_coverage, 1),
            urgences_score=round(score_urgences, 1),
            density_score=round(score_density, 1),
            age_score=round(score_age, 1),
            risk_level=risk_level,
            weights_used=self.weights.copy()
        )
    
    
    @staticmethod
    def _categorize_risk(score: float) -> str:
        """Détermine la catégorie de risque selon le score"""
        for level, (min_score, max_score) in RISK_CATEGORIES.items():
            if min_score <= score < max_score:
                return level
        return 'CRITICAL'  # Si >= 75
    
    
    # ==================== SIMULATION ====================
    
    def simulate_scenario(
        self,
        current_metrics: TerritoryMetrics,
        new_coverage: Optional[float] = None,
        new_urgences: Optional[int] = None,
        new_density: Optional[float] = None,
        new_age: Optional[float] = None
    ) -> Tuple[RiskScore, RiskScore, Dict[str, float]]:
        """
        Simule l'impact de modifications des métriques
        
        Args:
            current_metrics: Métriques actuelles
            new_coverage: Nouveau taux couverture (si modifié)
            new_urgences: Nouveaux passages (si modifié)
            new_density: Nouvelle densité (si modifié)
            new_age: Nouveau % 65+ (si modifié)
        
        Returns:
            Tuple (score_actuel, score_simulé, deltas_par_composante)
        """
        # Score actuel
        current_score = self.compute_risk_score(current_metrics)
        
        # Métriques simulées
        simulated_metrics = TerritoryMetrics(
            code=current_metrics.code,
            name=current_metrics.name,
            coverage_rate=new_coverage if new_coverage is not None else current_metrics.coverage_rate,
            urgences_count=new_urgences if new_urgences is not None else current_metrics.urgences_count,
            population_density=new_density if new_density is not None else current_metrics.population_density,
            pct_65plus=new_age if new_age is not None else current_metrics.pct_65plus
        )
        
        # Score simulé
        simulated_score = self.compute_risk_score(simulated_metrics)
        
        # Calcul des deltas par composante
        deltas = {
            'total': simulated_score.total - current_score.total,
            'coverage': simulated_score.coverage_score - current_score.coverage_score,
            'urgences': simulated_score.urgences_score - current_score.urgences_score,
            'density': simulated_score.density_score - current_score.density_score,
            'age': simulated_score.age_score - current_score.age_score
        }
        
        return current_score, simulated_score, deltas
    
    
    def compute_batch_scores(
        self,
        metrics_list: list[TerritoryMetrics]
    ) -> pd.DataFrame:
        """
        Calcule les scores pour plusieurs territoires
        
        Returns:
            DataFrame avec colonnes : code, name, total_score, risk_level, etc.
        """
        results = []
        
        for metrics in metrics_list:
            score = self.compute_risk_score(metrics)
            results.append({
                'code': metrics.code,
                'name': metrics.name,
                'total_score': score.total,
                'risk_level': score.risk_level,
                'coverage_score': score.coverage_score,
                'urgences_score': score.urgences_score,
                'density_score': score.density_score,
                'age_score': score.age_score,
                # Métriques brutes
                'coverage_rate': metrics.coverage_rate,
                'urgences_count': metrics.urgences_count,
                'population_density': metrics.population_density,
                'pct_65plus': metrics.pct_65plus
            })
        
        return pd.DataFrame(results)






# """
# core/risk_analyzer.py - CLASSE PRINCIPALE (POC)
# Fetch + Calcul + Simulation en une seule classe
# """

# import pandas as pd
# import numpy as np
# from typing import Dict, List, Optional, Tuple
# from datetime import datetime
# import streamlit as st

# from app.utils.api_client import APIClient
# from app.config import SCORING_WEIGHTS


# class RiskAnalyzer:
#     """
#     Classe centrale du POC - Tout-en-un simplifié
    
#     Responsabilités :
#     1. Fetch données APIs → DataFrame unifié
#     2. Calcul score de risque composite
#     3. Simulation de scénarios
#     4. Exports pour visualisation
#     """
    
#     def __init__(self):
#         """Initialise avec cache Streamlit intégré"""
#         self.api_client = APIClient()
#         self._data: Optional[pd.DataFrame] = None
#         self._scores: Optional[pd.DataFrame] = None
#         self.last_update: Optional[datetime] = None
    
    
#     # ==================== 1. FETCH DONNÉES ====================
    
#     @st.cache_data(ttl=3600)  # Cache 1h
#     def load_data(_self, date_start: str = "2024-01-01") -> pd.DataFrame:
#         """
#         Charge et fusionne TOUTES les données depuis APIs
        
#         Returns:
#             DataFrame unifié avec colonnes :
#             - code (str) : Code INSEE département
#             - name (str) : Nom département
#             - date (str) : YYYY-MM-DD
#             - coverage_rate (float) : Taux couverture (%)
#             - urgences_count (int) : Passages urgences
#             - population (int) : Population totale
#             - density (float) : Hab/km²
#             - pct_65plus (float) : % 65+ ans
#         """
#         # Fetch parallèle des 4 sources
#         df_coverage = _self.api_client.fetch_coverage_vaccinale()
#         df_urgences = _self.api_client.fetch_urgences()
#         df_demo = _self.api_client.fetch_demographie_insee()
        
#         # Extraire année pour merge (dates exactes différentes)
#         df_coverage['year'] = pd.to_datetime(df_coverage['date']).dt.year
#         df_urgences['year'] = pd.to_datetime(df_urgences['date']).dt.year
        
#         # Fusion sur (code, year) en conservant toutes les années de couverture (inclut 2024)
#         data = pd.merge(
#             df_coverage,
#             df_urgences[['code', 'year', 'date', 'urgences_count']],
#             on=['code', 'year'],
#             how='left',
#             suffixes=('', '_urg')
#         )
#         data = pd.merge(data, df_demo, on='code', how='left')
        
#         # Colonnes doublons
#         if 'date_urg' in data.columns:
#             data = data.drop(columns=['date_urg'])
        
#         # Imputation des urgences manquantes (ex: 2024) par report du dernier connu du territoire
#         data = data.sort_values(['code', 'year'])
#         data['urgences_count'] = data.groupby('code')['urgences_count'].ffill()
#         # Si toujours NaN (cas limite), remplacer par médiane globale
#         if data['urgences_count'].isna().any():
#             median_urg = data['urgences_count'].median()
#             data['urgences_count'] = data['urgences_count'].fillna(median_urg)
        
#         # Types
#         data['date'] = pd.to_datetime(data['date'])
        
#         _self._data = data
#         _self.last_update = datetime.now()
        
#         return data
    
    
#     # ==================== 2. CALCUL SCORES ====================
    
#     def compute_risk_scores(self, data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
#         """
#         Calcule le score de risque composite pour chaque territoire
        
#         Formule : Score = Σ(weight_i × score_i)
#         - score_coverage : Plus faible = plus risqué
#         - score_urgences : Plus élevé = plus risqué
#         - score_density : Plus dense = plus risqué
#         - score_age : Plus de 65+ = plus risqué
        
#         Returns:
#             DataFrame avec colonnes score_* et risk_level
#         """
#         if data is None:
#             data = self._data
        
#         df = data.copy()
        
#         # Normalisation des scores (0-100, 100 = risque max)
#         df['score_coverage'] = self._normalize_coverage(df['coverage_rate'])
#         df['score_urgences'] = self._normalize_urgences(df['urgences_count'])
#         df['score_density'] = self._normalize_density(df['density'])
#         df['score_age'] = self._normalize_age(df['pct_65plus'])
        
#         # Score composite
#         df['risk_score'] = (
#             SCORING_WEIGHTS['coverage'] * df['score_coverage'] +
#             SCORING_WEIGHTS['urgences'] * df['score_urgences'] +
#             SCORING_WEIGHTS['density'] * df['score_density'] +
#             SCORING_WEIGHTS['age'] * df['score_age']
#         )
        
#         # Catégorie de risque
#         df['risk_level'] = pd.cut(
#             df['risk_score'],
#             bins=[0, 25, 50, 75, 100],
#             labels=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
#         )
        
#         self._scores = df
#         return df
    
    
#     # ---------- Méthodes de normalisation ----------
    
#     @staticmethod
#     def _normalize_coverage(coverage: pd.Series) -> pd.Series:
#         """Plus la couverture est faible, plus le score est élevé"""
#         # Formule : score = 100 - (coverage × k) avec seuil 75%
#         return np.clip(100 - (coverage * 1.33), 0, 100)
    
#     @staticmethod
#     def _normalize_urgences(urgences: pd.Series) -> pd.Series:
#         """Normalisation min-max sur les passages urgences"""
#         # On compare à la médiane nationale
#         median = urgences.median()
#         ratio = urgences / median
#         return np.clip(ratio * 50, 0, 100)
    
#     @staticmethod
#     def _normalize_density(density: pd.Series) -> pd.Series:
#         """Densité normalisée : plus dense = score plus élevé"""
#         # Log-scale pour densité (écarts importants entre rural/urbain)
#         log_density = np.log1p(density)
#         return (log_density / log_density.max()) * 100
    
#     @staticmethod
#     def _normalize_age(pct_65plus: pd.Series) -> pd.Series:
#         """% 65+ normalisé : plus élevé = plus vulnérable"""
#         return np.clip((pct_65plus / 30) * 100, 0, 100)  # 30% = max théorique
    
    
#     # ==================== 3. REQUÊTES ====================
    
#     def get_score_by_territory(
#         self,
#         code: str,
#         date: Optional[str] = None
#     ) -> Dict:
#         """
#         Obtient le score d'un territoire spécifique
        
#         Returns:
#             {
#                 'risk_score': 78.5,
#                 'risk_level': 'HIGH',
#                 'details': {
#                     'coverage': 45.2,
#                     'urgences': 1250,
#                     'density': 5200,
#                     'pct_65plus': 22.5
#                 },
#                 'scores_detail': {
#                     'score_coverage': 65.0,
#                     'score_urgences': 82.0,
#                     ...
#                 }
#             }
#         """
#         if self._scores is None:
#             self.compute_risk_scores()
        
#         # Dernière date si non spécifiée
#         if date is None:
#             date = self._scores['date'].max()
        
#         row = self._scores[
#             (self._scores['code'] == code) &
#             (self._scores['date'] == date)
#         ]
        
#         if row.empty:
#             raise ValueError(f"Territoire {code} introuvable pour date {date}")
        
#         r = row.iloc[0]
        
#         return {
#             'code': code,
#             'name': r['name'],
#             'risk_score': round(r['risk_score'], 1),
#             'risk_level': r['risk_level'],
#             'details': {
#                 'coverage_rate': r['coverage_rate'],
#                 'urgences_count': int(r['urgences_count']),
#                 'population': int(r['population']),
#                 'density': round(r['density'], 1),
#                 'pct_65plus': round(r['pct_65plus'], 1)
#             },
#             'scores_detail': {
#                 'score_coverage': round(r['score_coverage'], 1),
#                 'score_urgences': round(r['score_urgences'], 1),
#                 'score_density': round(r['score_density'], 1),
#                 'score_age': round(r['score_age'], 1)
#             }
#         }
    
    
#     def get_all_scores(
#         self,
#         date: Optional[str] = None,
#         level: str = 'departmental'
#     ) -> pd.DataFrame:
#         """
#         Retourne tous les scores pour une date (pour carte)
#         """
#         if self._scores is None:
#             self.compute_risk_scores()
        
#         if date is None:
#             date = self._scores['date'].max()
        
#         return self._scores[
#             self._scores['date'] == date
#         ][['code', 'name', 'risk_score', 'risk_level', 
#            'coverage_rate', 'urgences_count']].copy()
    
    
#     def get_top_risks(self, n: int = 10, date: Optional[str] = None) -> pd.DataFrame:
#         """Top N territoires les plus à risque"""
#         scores = self.get_all_scores(date)
#         return scores.nlargest(n, 'risk_score')
    
    
#     # ==================== 4. SIMULATION ====================
    
#     def simulate_coverage_change(
#         self,
#         code: str,
#         new_coverage: float,
#         date: Optional[str] = None
#     ) -> Dict:
#         """
#         Simule l'impact d'un changement de couverture
        
#         Returns:
#             {
#                 'current_score': 78.5,
#                 'new_score': 62.3,
#                 'delta': -16.2,
#                 'new_risk_level': 'MEDIUM'
#             }
#         """
#         current = self.get_score_by_territory(code, date)
        
#         # Nouveau score de couverture
#         new_score_cov = self._normalize_coverage(pd.Series([new_coverage])).iloc[0]
        
#         # Recalcul du score total
#         old_score_cov = current['scores_detail']['score_coverage']
#         delta_cov = (new_score_cov - old_score_cov) * SCORING_WEIGHTS['coverage']
        
#         new_total = current['risk_score'] + delta_cov
        
#         # Nouvelle catégorie
#         new_level = pd.cut(
#             [new_total],
#             bins=[0, 25, 50, 75, 100],
#             labels=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
#         )[0]
        
#         return {
#             'current_score': current['risk_score'],
#             'current_coverage': current['details']['coverage_rate'],
#             'new_score': round(new_total, 1),
#             'new_coverage': new_coverage,
#             'delta': round(delta_cov, 1),
#             'new_risk_level': new_level
#         }
    
    
#     # ==================== 5. COMPARAISON ====================
    
#     def compare_territories(
#         self,
#         codes: List[str],
#         date: Optional[str] = None
#     ) -> pd.DataFrame:
#         """
#         Compare plusieurs territoires
        
#         Returns:
#             DataFrame avec scores côte à côte
#         """
#         comparisons = []
#         for code in codes:
#             try:
#                 score_data = self.get_score_by_territory(code, date)
#                 comparisons.append({
#                     'Code': code,
#                     'Nom': score_data['name'],
#                     'Score Risque': score_data['risk_score'],
#                     'Niveau': score_data['risk_level'],
#                     'Couverture (%)': score_data['details']['coverage_rate'],
#                     'Urgences': score_data['details']['urgences_count'],
#                     'Densité': score_data['details']['density']
#                 })
#             except ValueError:
#                 continue
        
#         return pd.DataFrame(comparisons)
    
    
#     # ==================== 6. TIMELINE ====================
    
#     def get_evolution(self, code: str) -> pd.DataFrame:
#         """
#         Évolution temporelle d'un territoire
        
#         Returns:
#             DataFrame avec date, risk_score, risk_level
#         """
#         if self._scores is None:
#             self.compute_risk_scores()
        
#         return self._scores[
#             self._scores['code'] == code
#         ][['date', 'risk_score', 'risk_level', 'coverage_rate']].sort_values('date')