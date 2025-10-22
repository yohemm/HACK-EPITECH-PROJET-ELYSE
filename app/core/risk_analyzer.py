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