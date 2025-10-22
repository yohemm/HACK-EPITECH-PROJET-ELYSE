"""
EpiMap Explorer - Application principale
Focus : Scoring composite configurable + Simulation interactive
"""

import streamlit as st
import pandas as pd
from typing import Dict
from core.risk_analyzer import RiskAnalyzer
from components.map_view import display_risk_map
from components.controls import render_controls

from config import DEFAULT_SCORING_WEIGHTS, RISK_COLORS
from core.risk_analyzer import RiskAnalyzer, TerritoryMetrics, RiskScore
from components.scoring_controls import (
    render_scoring_weights_controls,
    display_weights_summary
)
from components.simulation_panel import (
    render_simulation_panel,
    display_simulation_summary
)


# ==================== CONFIGURATION PAGE ====================

st.set_page_config(
    page_title="EpiMap Explorer - Scoring & Simulation",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Titre
st.title("EpiMap Explorer - Analyse des Risques Épidémiologiques")

# ==================== CSS CUSTOM ====================

st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #7f8c8d;
        margin-bottom: 2rem;
    }
    .risk-badge {
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


# ==================== DONNÉES DEMO ====================

@st.cache_data
def load_demo_data() -> pd.DataFrame:
    """
    Charge des données de démonstration
    En production, remplacer par fetch APIs
    """
    return pd.DataFrame({
        'code': ['75', '13', '69', '59', '33', '44', '31', '67', '34', '76'],
        'name': [
            'Paris', 'Bouches-du-Rhône', 'Rhône', 'Nord', 'Gironde',
            'Loire-Atlantique', 'Haute-Garonne', 'Bas-Rhin', 'Hérault', 'Seine-Maritime'
        ],
        'coverage_rate': [68.5, 55.2, 62.3, 48.7, 58.9, 63.1, 61.5, 52.8, 54.6, 57.3],
        'urgences_count': [1850, 980, 1120, 1450, 720, 650, 890, 1050, 780, 920],
        'population_density': [20754, 387, 635, 450, 162, 348, 689, 232, 175, 245],
        'pct_65plus': [17.2, 19.8, 15.6, 18.9, 21.3, 16.4, 14.8, 17.9, 20.5, 19.1]
    })


def create_territory_metrics(row: pd.Series) -> TerritoryMetrics:
    """Convertit une ligne DataFrame en TerritoryMetrics"""
    return TerritoryMetrics(
        code=row['code'],
        name=row['name'],
        coverage_rate=row['coverage_rate'],
        urgences_count=int(row['urgences_count']),
        population_density=row['population_density'],
        pct_65plus=row['pct_65plus']
    )


# ==================== STATE MANAGEMENT ====================

if 'weights' not in st.session_state:
    st.session_state.weights = DEFAULT_SCORING_WEIGHTS.copy()

if 'analyzer' not in st.session_state:
    st.session_state.analyzer = RiskAnalyzer(st.session_state.weights)

# ==================== HEADER ====================

st.markdown('<h1 class="main-title">🎯 EpiMap Explorer</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Scoring Composite Configurable & Simulation Interactive</p>',
    unsafe_allow_html=True
)

st.divider()


# ==================== SIDEBAR : CONFIGURATION GLOBALE ====================

with st.sidebar:
    st.title("⚙️ Configuration Globale")
    # Afficher des années propres et option "Toutes"
    # data['date'] = pd.to_datetime('2025-01-01')
    # year_list = sorted(data['date'].dt.year.unique().tolist())
    # year_options = ['Toutes'] + year_list if year_list else []
    # selected_year = st.selectbox("Année", year_options, index=0 if year_options else None)
    # selected_date = None if selected_year == 'Toutes' else pd.Timestamp(f"{selected_year}-01-01")
    demo_dates = pd.DataFrame({
      'date': pd.to_datetime(['2025-01-01', '2025-01-01', '2025-01-01'])
    })

    year_list = sorted(demo_dates['date'].dt.year.unique().tolist())
    year_options = ['Toutes'] + year_list
    selected_year = st.selectbox("Année", year_options, index=0)
    selected_date = None if selected_year == 'Toutes' else pd.Timestamp(f"{selected_year}-01-01")

    # selected_year = 'Toutes'
    # selected_date = None
    
    # show_simulation = st.checkbox("Activer mode simulation", value=False)
    
    # Section 1 : Poids du scoring
    with st.expander("⚖️ Poids du Scoring", expanded=False):
        new_weights = render_scoring_weights_controls(
            st.session_state.weights,
            key_prefix="global"
        )
        
        # Bouton pour appliquer les nouveaux poids
        if st.button("✅ Appliquer les Nouveaux Poids", type="primary"):
            # Vérifier que la somme = 1.0
            if abs(sum(new_weights.values()) - 1.0) < 0.01:
                st.session_state.weights = new_weights
                st.session_state.analyzer.update_weights(new_weights)
                st.success("✅ Poids mis à jour !")
                st.rerun()
            else:
                st.error("❌ La somme des poids doit être 1.0")
    
    st.divider()
    
    # Résumé des poids actuels
    st.markdown("### Poids Actuels")
    display_weights_summary(st.session_state.weights)
    
    st.divider()
    
    # Section 2 : Informations
    with st.expander("ℹ️ À propos"):
        st.markdown("""
        **EpiMap Explorer** est une plateforme de calcul de score de risque 
        épidémiologique composite.
        
        **Formule :**
```
        Score = w₁×S_cov + w₂×S_urg + w₃×S_den + w₄×S_age
```
        
        Où chaque score S est normalisé entre 0-100.
        """)


# ==================== MAIN CONTENT ====================

# Chargement des données
data = load_demo_data()

# Calcul des scores pour tous les territoires
metrics_list = [create_territory_metrics(row) for _, row in data.iterrows()]
scores_df = st.session_state.analyzer.compute_batch_scores(metrics_list)


# ==================== TABS ====================

tab1, tab2, tab3 = st.tabs([
    "📊 Vue d'Ensemble",
    "🎛️ Simulation Détaillée",
    "📈 Analyse Comparative"
])


# ========== TAB 1 : VUE D'ENSEMBLE ==========

with tab1:
    st.header("📊 Scores de Risque par Territoire")
    
    # Statistiques globales
    col1, col2, col3, col4 = st.columns([3,1,1,1])
    
    with col1:
        # Données carte: agrégation si "Toutes"
        # if selected_year == 'Toutes':
        #     df = analyzer._scores.copy()
        #     agg = (df.groupby(['code', 'name'], as_index=False)
        #              .agg(risk_score=('risk_score', 'mean'),
        #                   coverage_rate=('coverage_rate', 'mean'),
        #                   urgences_count=('urgences_count', 'mean')))
        #     # Recalcul de la catégorie de risque sur la moyenne
        #     agg['risk_level'] = pd.cut(
        #         agg['risk_score'], bins=[0, 25, 50, 75, 100], labels=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        #     )
        #     scores_data = agg
        # else:
        #     scores_data = analyzer.get_all_scores(date=selected_date)
        scores_data = scores_df
        display_risk_map(scores_data, height=200)
        st.metric(
            "Score Moyen National",
            f"{scores_df['total_score'].mean():.1f}",
            help="Moyenne pondérée de tous les territoires"
        )
    
    with col2:
        high_risk_count = len(scores_df[scores_df['risk_level'].isin(['HIGH', 'CRITICAL'])])
        st.metric(
            "Territoires à Risque Élevé",
            high_risk_count,
            help="Départements avec niveau HIGH ou CRITICAL"
        )
    
    with col3:
        st.metric(
            "Couverture Moyenne",
            f"{scores_df['coverage_rate'].mean():.1f}%",
            help="Taux de couverture vaccinale moyen"
        )
    
    with col4:
        st.metric(
            "Urgences Totales",
            f"{scores_df['urgences_count'].sum():,}",
            help="Total des passages aux urgences"
        )
    
    st.divider()
    
    # Tableau des scores
    st.subheader("Classement des Territoires")
    
    # Fonction pour colorer les cellules selon le niveau de risque
    def color_risk_level(val):
        color = RISK_COLORS.get(val, '#95a5a6')
        return f'background-color: {color}; color: white; font-weight: bold;'
    
    # Préparer le DataFrame pour affichage
    display_df = scores_df[[
        'name', 'total_score', 'risk_level',
        'coverage_rate', 'urgences_count', 'population_density', 'pct_65plus'
    ]].copy()
    
    display_df.columns = [
        'Territoire', 'Score Total', 'Niveau de Risque',
        'Couverture (%)', 'Urgences', 'Densité (hab/km²)', '% 65+'
    ]
    
    # Trier par score décroissant
    display_df = display_df.sort_values('Score Total', ascending=False)
    
    # Appliquer le style
    styled_df = display_df.style.applymap(
        color_risk_level,
        subset=['Niveau de Risque']
    ).format({
        'Score Total': '{:.1f}',
        'Couverture (%)': '{:.1f}',
        'Urgences': '{:,.0f}',
        'Densité (hab/km²)': '{:,.0f}',
        '% 65+': '{:.1f}'
    })
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Graphique de distribution des scores
    st.subheader("Distribution des Scores")
    
    import plotly.express as px
    
    fig = px.histogram(
        scores_df,
        x='total_score',
        nbins=20,
        title="Distribution des Scores de Risque",
        labels={'total_score': 'Score de Risque', 'count': 'Nombre de Territoires'},
        color_discrete_sequence=['#3498db']
# =======
    
#     with col2:
#         st.subheader("🚨 Top 5 Risques")
#         if selected_year == 'Toutes':
#             top = (scores_data.sort_values('risk_score', ascending=False)
#                               .head(5)[['name', 'risk_score', 'risk_level']])
#         else:
#             top = analyzer.get_top_risks(5, selected_date)
#         st.dataframe(top[['name', 'risk_score', 'risk_level']])
        
#         if show_simulation and selected_year != 'Toutes':
#             st.subheader("🎛️ Simulation")
#             selected_code = st.selectbox("Région", top['code'])
#             new_coverage = st.slider("Nouvelle couverture (%)", 0, 100, 60)
            
#             sim = analyzer.simulate_coverage_change(
#                 selected_code, 
#                 new_coverage, 
#                 selected_date
#             )
            
#             st.metric(
#                 "Score de risque",
#                 sim['new_score'],
#                 delta=sim['delta']
#             )
#         elif show_simulation and selected_year == 'Toutes':
#             st.info("La simulation est disponible lorsqu'une année précise est sélectionnée.")

# with tab2:
#     st.subheader("📊 Comparateur de Territoires")
#     code_options = analyzer._scores['code'].unique().tolist()
#     default_codes = code_options[:2] if len(code_options) >= 2 else code_options
#     codes = st.multiselect(
#         "Sélectionner régions",
#         code_options,
#         default=default_codes
# >>>>>>> origin/develop
    )
    
    fig.add_vline(x=25, line_dash="dash", line_color="green", annotation_text="LOW/MEDIUM")
    fig.add_vline(x=50, line_dash="dash", line_color="orange", annotation_text="MEDIUM/HIGH")
    fig.add_vline(x=75, line_dash="dash", line_color="red", annotation_text="HIGH/CRITICAL")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Graphique des composantes par territoire
    st.subheader("Décomposition des Scores par Composante")
    
    # Préparer les données pour graphique empilé
    components_df = scores_df[['name', 'coverage_score', 'urgences_score', 'density_score', 'age_score']].copy()
    components_df = components_df.sort_values('name')
    
    fig_components = px.bar(
        components_df,
        x='name',
        y=['coverage_score', 'urgences_score', 'density_score', 'age_score'],
        title="Contribution de Chaque Composante au Score Total",
        labels={'value': 'Score', 'name': 'Territoire', 'variable': 'Composante'},
        color_discrete_map={
            'coverage_score': '#3498db',
            'urgences_score': '#e74c3c',
            'density_score': '#f39c12',
            'age_score': '#9b59b6'
        },
        barmode='stack'
    )
    
    fig_components.update_layout(
        xaxis_tickangle=-45,
        legend_title_text='Composantes',
        yaxis_range=[0, 100]
    )
    
    st.plotly_chart(fig_components, use_container_width=True)


# ========== TAB 2 : SIMULATION DÉTAILLÉE ==========

with tab2:
    st.header("🎛️ Simulation Interactive par Territoire")
    
    st.markdown("""
    Sélectionnez un territoire et ajustez les paramètres pour simuler l'impact 
    sur le score de risque.
    """)
    
    # Sélection du territoire
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_territory = st.selectbox(
            "Sélectionner un territoire",
            options=data['code'].tolist(),
            format_func=lambda x: f"{data[data['code'] == x]['name'].values[0]} ({x})",
            key="territory_selector"
        )
    
    with col2:
        # Afficher le score actuel du territoire sélectionné
        current_row = scores_df[scores_df['code'] == selected_territory].iloc[0]
        
        risk_color = RISK_COLORS[current_row['risk_level']]
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {risk_color};">
            <strong>Score Actuel :</strong> {current_row['total_score']:.1f}<br>
            <strong>Niveau :</strong> <span class="risk-badge" style="background-color: {risk_color};">
                {current_row['risk_level']}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Récupérer les métriques actuelles
    current_metrics = create_territory_metrics(
        data[data['code'] == selected_territory].iloc[0]
    )
    
    # Panel de simulation
    simulation_result = render_simulation_panel(
        analyzer=st.session_state.analyzer,
        territory_code=selected_territory,
        current_metrics=current_metrics
    )
    
    # Si simulation active, afficher résumé dans sidebar
    if simulation_result:
        current_score, simulated_score, deltas = simulation_result
        
        with st.sidebar:
            st.divider()
            st.markdown("### 🎯 Résultat Simulation")
            display_simulation_summary(simulated_score, deltas)


# ========== TAB 3 : ANALYSE COMPARATIVE ==========

with tab3:
    st.header("📈 Analyse Comparative Multi-Territoires")
    
    st.markdown("""
    Sélectionnez plusieurs territoires pour comparer leurs scores et composantes.
    """)
    
    # Sélection multiple
    selected_codes = st.multiselect(
        "Sélectionner les territoires à comparer",
        options=data['code'].tolist(),
        default=['75', '13', '69'],
        format_func=lambda x: f"{data[data['code'] == x]['name'].values[0]} ({x})"
    )
    
    if len(selected_codes) < 2:
        st.warning("⚠️ Sélectionnez au moins 2 territoires pour la comparaison")
    else:
        # Filtrer les données
        comparison_df = scores_df[scores_df['code'].isin(selected_codes)].copy()
        
        st.divider()
        
        # Tableau comparatif
        st.subheader("Tableau Comparatif")
        
        comp_display = comparison_df[[
            'name', 'total_score', 'risk_level',
            'coverage_score', 'urgences_score', 'density_score', 'age_score'
        ]].copy()
        
        comp_display.columns = [
            'Territoire', 'Score Total', 'Niveau',
            'Score Couverture', 'Score Urgences', 'Score Densité', 'Score Âge'
        ]
        
        styled_comp = comp_display.style.applymap(
            color_risk_level,
            subset=['Niveau']
        ).format({
            'Score Total': '{:.1f}',
            'Score Couverture': '{:.1f}',
            'Score Urgences': '{:.1f}',
            'Score Densité': '{:.1f}',
            'Score Âge': '{:.1f}'
        }).background_gradient(
            subset=['Score Total'],
            cmap='RdYlGn_r'  # Rouge = score élevé, Vert = score faible
        )
        
        st.dataframe(styled_comp, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Graphique radar comparatif
        st.subheader("Graphique Radar Comparatif")
        
        import plotly.graph_objects as go
        
        fig_radar = go.Figure()
        
        categories = ['Couverture', 'Urgences', 'Densité', 'Âge']
        
        colors = ['#3498db', '#e74c3c', '#f39c12', '#9b59b6', '#2ecc71', '#e67e22']
        
        for idx, (_, row) in enumerate(comparison_df.iterrows()):
            fig_radar.add_trace(go.Scatterpolar(
                r=[
                    row['coverage_score'],
                    row['urgences_score'],
                    row['density_score'],
                    row['age_score']
                ],
                theta=categories,
                fill='toself',
                name=row['name'],
                line=dict(color=colors[idx % len(colors)])
            ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title="Comparaison des Composantes de Risque",
            height=500
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
        
        st.divider()
        
        # Graphique en barres groupées
        st.subheader("Comparaison par Composante")
        
        import plotly.express as px
        
        # Préparer données pour graphique
        melted_df = comparison_df.melt(
            id_vars=['name'],
            value_vars=['coverage_score', 'urgences_score', 'density_score', 'age_score'],
            var_name='Composante',
            value_name='Score'
        )
        
        # Renommer les composantes
        component_labels = {
            'coverage_score': 'Couverture',
            'urgences_score': 'Urgences',
            'density_score': 'Densité',
            'age_score': 'Âge'
        }
        melted_df['Composante'] = melted_df['Composante'].map(component_labels)
        
        fig_bars = px.bar(
            melted_df,
            x='Composante',
            y='Score',
            color='name',
            barmode='group',
            title="Scores par Composante et Territoire",
            labels={'name': 'Territoire', 'Score': 'Score (0-100)'},
            color_discrete_sequence=colors
        )
        
        fig_bars.update_layout(height=400)
        
        st.plotly_chart(fig_bars, use_container_width=True)
        
        st.divider()
        
        # Analyse des écarts
        st.subheader("Analyse des Écarts")
        
        # Calculer écart-type et moyennes
        stats = comparison_df[['coverage_score', 'urgences_score', 'density_score', 'age_score']].agg(['mean', 'std'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Moyennes des Composantes**")
            for comp in stats.columns:
                comp_label = component_labels[comp]
                mean_val = stats.loc['mean', comp]
                st.metric(comp_label, f"{mean_val:.1f}")
        
        with col2:
            st.markdown("**Écarts-Types**")
            for comp in stats.columns:
                comp_label = component_labels[comp]
                std_val = stats.loc['std', comp]
                st.metric(comp_label, f"{std_val:.1f}")


# ==================== FOOTER ====================

st.divider()

st.markdown("""
<div style="text-align: center; color: #7f8c8d; padding: 20px;">
    <p><strong>EpiMap Explorer</strong> - Plateforme de Scoring Épidémiologique</p>
    <p>Version POC - Focus : Scoring Composite & Simulation Interactive</p>
</div>
""", unsafe_allow_html=True)