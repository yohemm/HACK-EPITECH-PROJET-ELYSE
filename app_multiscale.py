"""
Page principale - Carte Multi-Échelle Interactive
France → Région → Département
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from app.core.risk_analyzer import RiskAnalyzer
from app.core.geo_data import GeoDataManager
from app.components.multi_scale_map import render_multiscale_map

st.set_page_config(
    page_title="EpiMap - Carte Multi-Échelle",
    page_icon="🗺️",
    layout="wide"
)

# CSS custom
import os
css_path = 'assets/custom.css'
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Titre principal
st.title("🗺️ Carte Interactive Multi-Échelle")
st.caption("Navigation: France → Régions → Départements")

# Initialisation des managers
@st.cache_resource
def get_managers():
    """Init managers (cached)"""
    analyzer = RiskAnalyzer()
    geo_manager = GeoDataManager()
    return analyzer, geo_manager

analyzer, geo_manager = get_managers()

# Chargement des données
@st.cache_data(ttl=1800)
def load_and_compute_data():
    """Charge données et calcule scores"""
    analyzer.load_data()
    analyzer.compute_risk_scores()
    return analyzer._data, analyzer._scores

try:
    data_raw, scores = load_and_compute_data()
    last_update = datetime.now().strftime("%d/%m/%Y %H:%M")
except Exception as e:
    st.error(f"Erreur chargement données: {e}")
    st.stop()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("⚙️ Paramètres")
    
    # Sélection date
    available_dates = sorted(scores['date'].unique(), reverse=True)
    if available_dates:
        selected_date = st.selectbox(
            "📅 Date d'analyse",
            options=available_dates,
            format_func=lambda x: pd.to_datetime(x).strftime("%d/%m/%Y")
        )
    else:
        selected_date = scores['date'].max()
    
    st.divider()
    
    # Métriques affichées
    st.subheader("📊 Indicateurs")
    show_coverage = st.checkbox("💉 Couverture vaccinale", value=True)
    show_urgences = st.checkbox("🚑 Passages urgences", value=True)
    show_demo = st.checkbox("👥 Démographie", value=True)
    
    st.divider()
    
    # Filtres
    st.subheader("🔍 Filtres")
    
    min_risk = st.slider(
        "Score de risque minimum",
        min_value=0,
        max_value=100,
        value=0,
        step=5
    )
    
    risk_levels_filter = st.multiselect(
        "Niveaux de risque",
        options=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
        default=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    )
    
    st.divider()
    
    # Infos
    st.caption(f"🔄 Dernière mise à jour: {last_update}")
    st.caption(f"📊 {len(scores)} territoires analysés")

# ==================== ÉTAT DE NAVIGATION ====================
# Initialiser état session
if 'map_level' not in st.session_state:
    st.session_state['map_level'] = 'regional'  # Par défaut: vue régions

if 'selected_region' not in st.session_state:
    st.session_state['selected_region'] = None

current_level = st.session_state['map_level']
selected_region = st.session_state['selected_region']

# ==================== PRÉPARATION DES DONNÉES ====================
# Filtrer par date
scores_filtered = scores[scores['date'] == selected_date].copy()

# Filtrer par risque
scores_filtered = scores_filtered[
    (scores_filtered['risk_score'] >= min_risk) &
    (scores_filtered['risk_level'].isin(risk_levels_filter))
]

# Agréger selon niveau
value_cols = ['coverage_rate', 'urgences_count', 'risk_score']

if current_level == 'regional':
    # Vue régions
    display_data = geo_manager.aggregate_to_region(
        scores_filtered,
        value_cols=value_cols,
        weighted_by='population'
    )
    display_data['level'] = 'regional'
    
elif current_level == 'departmental':
    # Vue départements (d'une région ou tous)
    display_data = geo_manager.get_hierarchy_data(
        scores_filtered,
        value_cols=value_cols,
        current_level='departmental',
        selected_region=selected_region
    )
    display_data['level'] = 'departmental'
    
else:  # national
    display_data = scores_filtered.copy()
    display_data['level'] = 'departmental'

# ==================== KPIs ====================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "🏥 Territoires",
        len(display_data),
        help="Nombre de territoires affichés"
    )

with col2:
    critical_count = (display_data['risk_level'] == 'CRITICAL').sum() if 'risk_level' in display_data.columns else 0
    st.metric(
        "🚨 Risque critique",
        critical_count,
        delta=f"{critical_count/len(display_data)*100:.1f}%" if len(display_data) > 0 else "0%"
    )

with col3:
    avg_coverage = display_data['coverage_rate'].mean() if 'coverage_rate' in display_data.columns else 0
    st.metric(
        "💉 Couverture moy.",
        f"{avg_coverage:.1f}%",
        delta=f"{avg_coverage - 75:.1f}%" if avg_coverage > 0 else "N/A"
    )

with col4:
    total_urgences = display_data['urgences_count'].sum() if 'urgences_count' in display_data.columns else 0
    st.metric(
        "🚑 Urgences totales",
        f"{total_urgences:,.0f}"
    )

st.divider()

# ==================== CARTE PRINCIPALE ====================
st.subheader("📍 Carte Interactive")

# Colonnes pour carte + détails
col_map, col_details = st.columns([3, 1])

with col_map:
    # Afficher carte multi-échelle
    map_interactions = render_multiscale_map(
        data=display_data,
        geo_manager=geo_manager,
        current_level=current_level,
        selected_region=selected_region
    )

with col_details:
    st.markdown("### 📋 Top Risques")
    
    if not display_data.empty:
        top_risks = display_data.nlargest(5, 'risk_score')[
            ['name', 'risk_score', 'coverage_rate']
        ].copy()
        
        top_risks = top_risks.rename(columns={
            'name': 'Territoire',
            'risk_score': 'Score',
            'coverage_rate': 'Couverture %'
        })
        
        st.dataframe(
            top_risks,
            hide_index=True,
            use_container_width=True
        )
        
        # Boutons de navigation rapide
        st.markdown("#### 🔍 Explorer")
        
        if current_level == 'regional':
            st.markdown("Cliquez sur une région pour voir ses départements")
            
            # Liste régions avec boutons
            for _, row in top_risks.head(3).iterrows():
                terr_name = row['Territoire']
                # Trouver code région
                region_code = None
                for code, name in geo_manager.region_names.items():
                    if name == terr_name:
                        region_code = code
                        break
                
                if region_code and st.button(f"➡️ {terr_name}", key=f"nav_{region_code}"):
                    st.session_state['map_level'] = 'departmental'
                    st.session_state['selected_region'] = region_code
                    st.rerun()
    else:
        st.info("Aucune donnée à afficher avec les filtres actuels")

# ==================== TABLEAUX DÉTAILLÉS ====================
st.divider()

with st.expander("📊 Données détaillées", expanded=False):
    if not display_data.empty:
        # Préparer colonnes à afficher
        cols_to_show = ['code', 'name', 'risk_score', 'risk_level']
        
        if show_coverage and 'coverage_rate' in display_data.columns:
            cols_to_show.append('coverage_rate')
        
        if show_urgences and 'urgences_count' in display_data.columns:
            cols_to_show.append('urgences_count')
        
        if show_demo and 'population' in display_data.columns:
            cols_to_show.extend(['population', 'density', 'pct_65plus'])
        
        # Filtrer colonnes existantes
        cols_to_show = [c for c in cols_to_show if c in display_data.columns]
        
        display_table = display_data[cols_to_show].copy()
        
        # Renommer pour affichage
        display_table = display_table.rename(columns={
            'code': 'Code',
            'name': 'Nom',
            'risk_score': 'Score Risque',
            'risk_level': 'Niveau',
            'coverage_rate': 'Couverture %',
            'urgences_count': 'Urgences',
            'population': 'Population',
            'density': 'Densité',
            'pct_65plus': '% 65+'
        })
        
        st.dataframe(
            display_table,
            use_container_width=True,
            hide_index=True
        )
        
        # Export CSV
        csv = display_table.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger CSV",
            data=csv,
            file_name=f"epimap_data_{selected_date}_{current_level}.csv",
            mime="text/csv"
        )
    else:
        st.warning("Aucune donnée disponible")

# ==================== LÉGENDE ET AIDE ====================
with st.expander("ℹ️ Guide d'utilisation"):
    st.markdown("""
    ### Navigation Multi-Échelle
    
    1. **Vue France (Régions)** : Vue d'ensemble des 13 régions métropolitaines + 5 DOM
        - Cliquez sur une région pour zoomer
        - Comparez les scores entre régions
    
    2. **Vue Départements** : Détail d'une région sélectionnée
        - Visualisez tous les départements de la région
        - Identifiez les zones à risque
        - Retour : cliquez sur le bouton région en haut
    
    ### Indicateurs
    
    - **💉 Couverture vaccinale** : Taux de vaccination contre la grippe (source: Santé Publique France)
    - **🚑 Passages aux urgences** : Nombre de passages liés à la grippe (source: OSCOUR)
    - **👥 Démographie** : Population, densité, structure par âge (source: INSEE)
    - **📊 Score de risque** : Score composite 0-100 calculé à partir des 4 indicateurs pondérés
    
    ### Couleurs
    
    - 🟢 **Vert (0-25)** : Risque faible
    - 🟠 **Orange (25-50)** : Risque modéré
    - 🔴 **Rouge (50-75)** : Risque élevé
    - 🔴 **Rouge foncé (75-100)** : Risque critique - action urgente
    """)
