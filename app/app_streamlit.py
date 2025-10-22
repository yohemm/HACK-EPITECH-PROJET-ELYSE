"""
Application Streamlit - POC EpiMap Explorer
"""

import streamlit as st
import pandas as pd
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
st.title("EpiMap Explorer - Analyse des Risques Épidémiologiques")

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
    # Afficher des années propres et option "Toutes"
    date_series = pd.to_datetime(analyzer._scores['date'])
    year_list = sorted(date_series.dt.year.unique().tolist())
    year_options = ['Toutes'] + year_list if year_list else []
    selected_year = st.selectbox("Année", year_options, index=0 if year_options else None)
    selected_date = None if selected_year == 'Toutes' else pd.Timestamp(f"{selected_year}-01-01")
    
    show_simulation = st.checkbox("Activer mode simulation", value=False)

# Layout principal
tab1, tab2, tab3 = st.tabs(["Carte", "Comparateur", "Timeline"])

with tab1:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Données carte: agrégation si "Toutes"
        if selected_year == 'Toutes':
            df = analyzer._scores.copy()
            agg = (df.groupby(['code', 'name'], as_index=False)
                     .agg(risk_score=('risk_score', 'mean'),
                          coverage_rate=('coverage_rate', 'mean'),
                          urgences_count=('urgences_count', 'mean')))
            # Recalcul de la catégorie de risque sur la moyenne
            agg['risk_level'] = pd.cut(
                agg['risk_score'], bins=[0, 25, 50, 75, 100], labels=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            )
            scores_data = agg
        else:
            scores_data = analyzer.get_all_scores(date=selected_date)
        display_risk_map(scores_data)  # Composant carte
    
    with col2:
        st.subheader("🚨 Top 5 Risques")
        if selected_year == 'Toutes':
            top = (scores_data.sort_values('risk_score', ascending=False)
                              .head(5)[['name', 'risk_score', 'risk_level']])
        else:
            top = analyzer.get_top_risks(5, selected_date)
        st.dataframe(top[['name', 'risk_score', 'risk_level']])
        
        if show_simulation and selected_year != 'Toutes':
            st.subheader("🎛️ Simulation")
            selected_code = st.selectbox("Région", top['code'])
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
        elif show_simulation and selected_year == 'Toutes':
            st.info("La simulation est disponible lorsqu'une année précise est sélectionnée.")

with tab2:
    st.subheader("📊 Comparateur de Territoires")
    code_options = analyzer._scores['code'].unique().tolist()
    default_codes = code_options[:2] if len(code_options) >= 2 else code_options
    codes = st.multiselect(
        "Sélectionner régions",
        code_options,
        default=default_codes
    )
    
    if codes:
        comparison = analyzer.compare_territories(codes, selected_date)
        st.dataframe(comparison)

with tab3:
    st.subheader("📈 Évolution Temporelle")
    code_timeline = st.selectbox("Région", code_options if 'code_options' in locals() else analyzer._scores['code'].unique())
    
    evolution = analyzer.get_evolution(code_timeline)
    st.line_chart(evolution.set_index('date')['risk_score'])