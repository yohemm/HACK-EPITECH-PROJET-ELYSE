"""
Application Streamlit - POC EpiMap Explorer
"""

import streamlit as st
from app.core.risk_analyzer import RiskAnalyzer
from app.components.map_view import display_risk_map
from app.components.controls import render_controls

st.set_page_config(
    page_title="EpiMap Explorer",
    page_icon="🗺️",
    layout="wide"
)

# CSS custom (optionnel)
import os
css_path = 'assets/custom.css'
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Titre
st.title("🗺️ EpiMap Explorer - Analyse des Risques Épidémiologiques")

# Init analyzer (cached)
@st.cache_resource
def get_analyzer():
    analyzer = RiskAnalyzer()
    analyzer.load_data()
    analyzer.compute_risk_scores()
    return analyzer

analyzer = get_analyzer()

# Sidebar contrôles
with st.sidebar:
    st.header("⚙️ Paramètres")
    selected_date = st.selectbox(
        "Date",
        analyzer._scores['date'].unique(),
        index=0
    )
    
    show_simulation = st.checkbox("Activer mode simulation", value=False)

# Layout principal
tab1, tab2, tab3 = st.tabs(["🗺️ Carte", "📊 Comparateur", "📈 Timeline"])

with tab1:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        scores_data = analyzer.get_all_scores(date=selected_date)
        display_risk_map(scores_data)  # Composant carte
    
    with col2:
        st.subheader("🚨 Top 5 Risques")
        top = analyzer.get_top_risks(5, selected_date)
        st.dataframe(top[['name', 'risk_score', 'risk_level']])
        
        if show_simulation:
            st.subheader("🎛️ Simulation")
            selected_code = st.selectbox("Département", top['code'])
            new_coverage = st.slider("Nouvelle couverture (%)", 0, 100, 60)
            
            sim = analyzer.simulate_coverage_change(
                selected_code, 
                new_coverage, 
                selected_date
            )
            
            st.metric(
                "Score de risque",
                sim['new_score'],
                delta=sim['delta']
            )

with tab2:
    st.subheader("📊 Comparateur de Territoires")
    codes = st.multiselect(
        "Sélectionner départements",
        analyzer._scores['code'].unique(),
        default=['75', '13']
    )
    
    if codes:
        comparison = analyzer.compare_territories(codes, selected_date)
        st.dataframe(comparison)

with tab3:
    st.subheader("📈 Évolution Temporelle")
    code_timeline = st.selectbox("Département", analyzer._scores['code'].unique())
    
    evolution = analyzer.get_evolution(code_timeline)
    st.line_chart(evolution.set_index('date')['risk_score'])