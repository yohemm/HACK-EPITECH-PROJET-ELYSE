"""
Composant Streamlit pour simulation locale des métriques
"""

import streamlit as st
from typing import Dict, Optional, Tuple

from config import SIMULATION_LIMITS, RISK_COLORS
from core.risk_analyzer import TerritoryMetrics, RiskScore

import numpy as np

def _scalar(value):
    """Convertit toute structure en float unique."""
    import numpy as np
    import pandas as pd

    if value is None:
        return 0.0

    # pandas
    if isinstance(value, (pd.Series, pd.DataFrame)):
        return float(np.nanmean(value.values))

    # numpy array, list, tuple
    if isinstance(value, (list, tuple, np.ndarray)):
        arr = np.array(value, dtype=float).flatten()
        if arr.size == 0:
            return 0.0
        return float(np.nanmean(arr))  # <-- conversion en float obligatoire

    # numpy scalar
    if isinstance(value, (np.generic,)):
        return float(value)

    # int/float direct
    return float(value)


def render_simulation_panel(
    analyzer,  # RiskAnalyzer instance
    territory_code: str,
    current_metrics: TerritoryMetrics
) -> Optional[Tuple[RiskScore, RiskScore, Dict]]:
    """
    Affiche le panel de simulation avec curseurs pour tous les paramètres
    
    Args:
        analyzer: Instance de RiskAnalyzer
        territory_code: Code du territoire
        current_metrics: Métriques actuelles du territoire
    
    Returns:
        Tuple (score_actuel, score_simulé, deltas) si simulation active,
        None sinon
    """
    st.subheader(f"🎛️ Simulation - {current_metrics.name}")
    
    st.markdown("""
    Ajustez les curseurs pour simuler l'impact de changements sur le score de risque.
    """)
    
    # Toggle simulation
    simulate = st.checkbox(
        "Activer la simulation",
        value=False,
        key=f"simulate_{territory_code}"
    )
    
    if not simulate:
        return None
    
    st.divider()
    
    # ========== CURSEURS DE SIMULATION ==========
    
    st.markdown("### 📊 Paramètres Simulés")
    
    # 1. Couverture Vaccinale
    st.markdown("#### 1️⃣ Couverture Vaccinale")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_coverage = st.slider(
            "Taux de couverture (%)",
            min_value=SIMULATION_LIMITS['coverage']['min'],
            max_value=SIMULATION_LIMITS['coverage']['max'],
            value=_scalar(current_metrics.coverage_rate),
            step=SIMULATION_LIMITS['coverage']['step'],
            key=f"sim_coverage_{territory_code}",
            help="Taux de vaccination de la population"
        )
    
    with col2:
        delta_cov = new_coverage - _scalar(current_metrics.coverage_rate)
        st.metric(
            "Δ Couverture",
            f"{delta_cov:+.1f}%",
            delta=f"{delta_cov:+.1f}%"
        )
    
    # 2. Passages aux Urgences
    st.markdown("#### 2️⃣ Passages aux Urgences")
    col1, col2 = st.columns([3, 1])

    with col1:
        new_urgences = st.slider(
            "Nombre de passages",
            min_value=SIMULATION_LIMITS['urgences']['min'],
            max_value=SIMULATION_LIMITS['urgences']['max'],
            value=int(_scalar(current_metrics.urgences_count)),
            step=SIMULATION_LIMITS['urgences']['step'],
            key=f"sim_urgences_{territory_code}",
            help="Passages aux urgences liés à la grippe"
        )
    with col2:
        delta_urg = int(new_urgences - _scalar(current_metrics.urgences_count))
        st.metric(
            "Δ Urgences",
            f"{delta_urg:+d}",
            delta=f"{delta_urg:+d}"
        )
    
    # 3. Densité de Population
    st.markdown("#### 3️⃣ Densité de Population")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_density = st.slider(
          "Densité (hab/km²)",
          min_value=SIMULATION_LIMITS['density']['min'],
          max_value=SIMULATION_LIMITS['density']['max'],
          value=int(_scalar(current_metrics.population_density)),
          step=SIMULATION_LIMITS['density']['step'],
          key=f"sim_density_{territory_code}",
          help="Habitants par km²",
          format="%.0f"
        )

    
    with col2:
        delta_den = new_density - _scalar(current_metrics.population_density)
        st.metric(
            "Δ Densité",
            f"{delta_den:+.0f}",
            delta=f"{delta_den:+.0f}"
        )
    
    # 4. Structure d'Âge
    st.markdown("#### 4️⃣ Structure d'Âge (% 65+)")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_age = st.slider(
            "Pourcentage de 65+ ans",
            min_value=SIMULATION_LIMITS['age_65plus']['min'],
            max_value=SIMULATION_LIMITS['age_65plus']['max'],
            value=_scalar(current_metrics.pct_65plus),
            step=SIMULATION_LIMITS['age_65plus']['step'],
            key=f"sim_age_{territory_code}",
            help="Part de la population âgée de 65 ans et plus"
        )
    
    with col2:
        delta_age = new_age - _scalar(current_metrics.pct_65plus)
        st.metric(
            "Δ Âge",
            f"{delta_age:+.1f}%",
            delta=f"{delta_age:+.1f}%"
        )
    
    st.divider()
    
    # ========== CALCUL DE LA SIMULATION ==========
    
    current_score, simulated_score, deltas = analyzer.simulate_scenario(
        current_metrics=current_metrics,
        new_coverage=new_coverage,
        new_urgences=new_urgences,
        new_density=new_density,
        new_age=new_age
    )
    
    # ========== AFFICHAGE DES RÉSULTATS ==========
    
    st.markdown("### 📈 Résultats de la Simulation")
    
    # Métriques principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Score Actuel",
            f"{current_score.total:.1f}",
            delta=None,
            help=f"Niveau : {current_score.risk_level}"
        )
    
    with col2:
        delta_color = "normal" if deltas['total'] < 0 else "inverse"
        st.metric(
            "Score Simulé",
            f"{simulated_score.total:.1f}",
            delta=f"{deltas['total']:+.1f}",
            delta_color=delta_color,
            help=f"Niveau : {simulated_score.risk_level}"
        )
    
    with col3:
        # Changement de niveau de risque
        if current_score.risk_level != simulated_score.risk_level:
            st.markdown(f"""
            **Changement de niveau :**  
            `{current_score.risk_level}` → `{simulated_score.risk_level}`
            """)
        else:
            st.markdown(f"""
            **Niveau maintenu :**  
            `{current_score.risk_level}`
            """)
    
    # Détails par composante
    with st.expander("🔍 Détails par Composante"):
        _display_component_comparison(current_score, simulated_score, deltas)
    
    # Graphique de comparaison
    _display_comparison_chart(current_score, simulated_score)
    
    return current_score, simulated_score, deltas


def _display_component_comparison(
    current: RiskScore,
    simulated: RiskScore,
    deltas: Dict[str, float]
) -> None:
    """Affiche le tableau de comparaison des composantes"""
    
    import pandas as pd
    
    comparison_data = {
        'Composante': [
            '📊 Couverture',
            '🏥 Urgences',
            '👥 Densité',
            '🎂 Âge',
            '🎯 TOTAL'
        ],
        'Score Actuel': [
            f"{current.coverage_score:.1f}",
            f"{current.urgences_score:.1f}",
            f"{current.density_score:.1f}",
            f"{current.age_score:.1f}",
            f"{current.total:.1f}"
        ],
        'Score Simulé': [
            f"{simulated.coverage_score:.1f}",
            f"{simulated.urgences_score:.1f}",
            f"{simulated.density_score:.1f}",
            f"{simulated.age_score:.1f}",
            f"{simulated.total:.1f}"
        ],
        'Δ': [
            f"{deltas['coverage']:+.1f}",
            f"{deltas['urgences']:+.1f}",
            f"{deltas['density']:+.1f}",
            f"{deltas['age']:+.1f}",
            f"{deltas['total']:+.1f}"
        ]
    }
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _display_comparison_chart(
    current: RiskScore,
    simulated: RiskScore
) -> None:
    """Graphique de comparaison radar"""
    
    import plotly.graph_objects as go
    
    categories = ['Couverture', 'Urgences', 'Densité', 'Âge']
    
    current_values = [
        current.coverage_score,
        current.urgences_score,
        current.density_score,
        current.age_score
    ]
    
    simulated_values = [
        simulated.coverage_score,
        simulated.urgences_score,
        simulated.density_score,
        simulated.age_score
    ]
    
    fig = go.Figure()
    
    # Score actuel
    fig.add_trace(go.Scatterpolar(
        r=current_values,
        theta=categories,
        fill='toself',
        name='Actuel',
        line=dict(color='#3498db')
    ))
    
    # Score simulé
    fig.add_trace(go.Scatterpolar(
        r=simulated_values,
        theta=categories,
        fill='toself',
        name='Simulé',
        line=dict(color='#e74c3c')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title="Comparaison des Composantes",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_simulation_summary(
    simulated_score: RiskScore,
    deltas: Dict[str, float]
) -> None:
    """
    Affiche un résumé compact de la simulation (pour sidebar)
    """
    # Badge coloré selon niveau
    risk_color = RISK_COLORS[simulated_score.risk_level]
    
    st.markdown(f"""
    <div style="
        background-color: {risk_color}20;
        border-left: 4px solid {risk_color};
        padding: 10px;
        margin: 10px 0;
    ">
        <strong>Score Simulé :</strong> {simulated_score.total:.1f}<br>
        <strong>Niveau :</strong> {simulated_score.risk_level}<br>
        <strong>Évolution :</strong> {deltas['total']:+.1f} points
    </div>
    """, unsafe_allow_html=True)