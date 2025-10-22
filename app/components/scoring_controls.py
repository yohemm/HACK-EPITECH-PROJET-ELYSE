"""
Composant Streamlit pour ajuster les poids du scoring
"""

import streamlit as st
from typing import Dict
import plotly.graph_objects as go

def render_scoring_weights_controls(
    current_weights: Dict[str, float],
    key_prefix: str = "weight"
) -> Dict[str, float]:
    """
    Affiche les contrôles pour ajuster les poids du scoring
    
    Args:
        current_weights: Poids actuels
        key_prefix: Préfixe pour les clés Streamlit (éviter conflits)
    
    Returns:
        Nouveaux poids ajustés (dict)
    """
    st.subheader("⚖️ Configuration des Poids")
    
    st.markdown("""
    Ajustez l'importance de chaque indicateur dans le calcul du score de risque.
    **La somme doit égaler 1.0 (100%)**
    """)
    
    # Sliders pour chaque poids
    new_weights = {}
    
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            new_weights['coverage'] = st.slider(
                "📊 Couverture Vaccinale",
                min_value=0.0,
                max_value=1.0,
                value=current_weights['coverage'],
                step=0.05,
                key=f"{key_prefix}_coverage",
                help="Poids de la couverture vaccinale dans le score final"
            )
            
            new_weights['urgences'] = st.slider(
                "🏥 Passages aux Urgences",
                min_value=0.0,
                max_value=1.0,
                value=current_weights['urgences'],
                step=0.05,
                key=f"{key_prefix}_urgences",
                help="Poids des passages aux urgences dans le score final"
            )
        
        with col2:
            new_weights['density'] = st.slider(
                "👥 Densité de Population",
                min_value=0.0,
                max_value=1.0,
                value=current_weights['density'],
                step=0.05,
                key=f"{key_prefix}_density",
                help="Poids de la densité de population dans le score final"
            )
            
            new_weights['age'] = st.slider(
                "🎂 Structure d'Âge (% 65+)",
                min_value=0.0,
                max_value=1.0,
                value=current_weights['age'],
                step=0.05,
                key=f"{key_prefix}_age",
                help="Poids de la structure d'âge dans le score final"
            )
    
    # Validation de la somme
    total = sum(new_weights.values())
    
    # Indicateur visuel de la somme
    if abs(total - 1.0) < 0.01:
        st.success(f"✅ Somme des poids : {total:.2f} (valide)")
    else:
        st.error(f"❌ Somme des poids : {total:.2f} (doit être 1.0)")
        st.warning("⚠️ Ajustez les curseurs pour que la somme égale 1.0")
    
    # Affichage visuel de la répartition
    # with st.expander("📊 Visualisation de la répartition"):
    #     # Diagramme en barres horizontal
    #     import plotly.graph_objects as go
        
    #     fig = go.Figure(go.Bar(
    #         x=list(new_weights.values()),
    #         y=list(new_weights.keys()),
    #         orientation='h',
    #         marker=dict(
    #             color=['#3498db', '#e74c3c', '#f39c12', '#9b59b6']
    #         )
    #     ))
        
    #     fig.update_layout(
    #         title="Répartition des Poids",
    #         xaxis_title="Poids",
    #         yaxis_title="Indicateur",
    #         height=300,
    #         showlegend=False
    #     )
        
    #     st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 📊 Visualisation de la répartition")

    fig = go.Figure(go.Bar(
        x=list(new_weights.values()),
        y=list(new_weights.keys()),
        orientation='h',
        marker=dict(color=['#3498db', '#e74c3c', '#f39c12', '#9b59b6'])
    ))
    fig.update_layout(
        title="Répartition des Poids",
        xaxis_title="Poids",
        yaxis_title="Indicateur",
        height=300,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    return new_weights


def display_weights_summary(weights: Dict[str, float]) -> None:
    """
    Affiche un résumé compact des poids actuels
    """
    st.markdown("**Poids actuels :**")
    
    cols = st.columns(4)
    
    labels = {
        'coverage': '📊 Couverture',
        'urgences': '🏥 Urgences',
        'density': '👥 Densité',
        'age': '🎂 Âge'
    }
    
    for i, (key, label) in enumerate(labels.items()):
        with cols[i]:
            st.metric(
                label=label,
                value=f"{weights[key]:.0%}"
            )