"""
Composants de contrôle (sidebar, filters, etc.)
"""

import streamlit as st
from typing import Dict, Any


def render_controls() -> Dict[str, Any]:
    """
    Affiche les contrôles de la sidebar
    
    Returns:
        Dict avec les paramètres sélectionnés
    """
    with st.sidebar:
        st.header("⚙️ Paramètres")
        
        # Sélection date
        selected_date = st.date_input(
            "Date d'analyse",
            value=None,
            help="Laisser vide pour la date la plus récente"
        )
        
        # Filtres de risque
        st.subheader("Filtres")
        risk_levels = st.multiselect(
            "Niveaux de risque",
            options=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
            default=['HIGH', 'CRITICAL'],
            help="Afficher uniquement ces niveaux sur la carte"
        )
        
        # Seuils personnalisés
        st.subheader("Seuils")
        coverage_threshold = st.slider(
            "Seuil couverture minimale (%)",
            min_value=0,
            max_value=100,
            value=75,
            step=5,
            help="Objectif OMS: 75%"
        )
        
        # Mode simulation
        st.divider()
        show_simulation = st.checkbox(
            "🎛️ Activer mode simulation",
            value=False,
            help="Simuler l'impact de changements de couverture"
        )
        
        # Export
        st.divider()
        if st.button("📥 Exporter les données"):
            st.info("Export CSV à implémenter")
        
        return {
            'selected_date': selected_date,
            'risk_levels': risk_levels,
            'coverage_threshold': coverage_threshold,
            'show_simulation': show_simulation
        }


def render_metrics(analyzer, date=None) -> None:
    """
    Affiche les KPIs principaux en haut de page
    
    Args:
        analyzer: Instance de RiskAnalyzer
        date: Date sélectionnée (None = dernière)
    """
    scores = analyzer.get_all_scores(date)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🏥 Départements analysés",
            value=len(scores)
        )
    
    with col2:
        critical_count = (scores['risk_level'] == 'CRITICAL').sum()
        st.metric(
            label="🚨 Risque critique",
            value=critical_count,
            delta=f"{critical_count/len(scores)*100:.1f}%"
        )
    
    with col3:
        avg_coverage = scores['coverage_rate'].mean()
        st.metric(
            label="💉 Couverture moyenne",
            value=f"{avg_coverage:.1f}%",
            delta=f"{avg_coverage - 75:.1f}% vs objectif"
        )
    
    with col4:
        total_urgences = scores['urgences_count'].sum()
        st.metric(
            label="🚑 Passages urgences",
            value=f"{total_urgences:,.0f}"
        )
