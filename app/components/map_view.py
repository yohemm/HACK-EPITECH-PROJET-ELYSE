"""
Composant carte interactive - Folium
"""

import folium
from folium.plugins import MarkerCluster
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from config import MAP_CONFIG


# Coordonnées départements (centroides approximatifs - top 20)
DEPT_COORDS = {
    '75': (48.8566, 2.3522),   # Paris
    '13': (43.2965, 5.3698),   # Marseille
    '69': (45.7640, 4.8357),   # Lyon
    '31': (43.6045, 1.4442),   # Toulouse
    '06': (43.7102, 7.2620),   # Nice
    '44': (47.2184, -1.5536),  # Nantes
    '33': (44.8378, -0.5792),  # Bordeaux
    '59': (50.6292, 3.0573),   # Lille
    '67': (48.5734, 7.7521),   # Strasbourg
    '34': (43.6108, 3.8767),   # Montpellier
    '35': (48.1173, -1.6778),  # Rennes
    '38': (45.1885, 5.7245),   # Grenoble
    '62': (50.4800, 2.7930),   # Arras
    '76': (49.4432, 1.0993),   # Rouen
    '92': (48.8906, 2.2395),   # Hauts-de-Seine
    '93': (48.9124, 2.4787),   # Seine-Saint-Denis
    '94': (48.7829, 2.4871),   # Val-de-Marne
    '78': (48.8044, 2.1301),   # Yvelines
    '77': (48.8467, 2.9742),   # Seine-et-Marne
    '91': (48.6333, 2.4417),   # Essonne
}


def get_color_for_risk(risk_score: float, risk_level: str = None) -> str:
    """
    Retourne une couleur selon le score de risque
    
    Args:
        risk_score: Score entre 0-100
        risk_level: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    
    Returns:
        Code couleur hex
    """
    if risk_level:
        color_map = {
            'LOW': '#2ecc71',      # Vert
            'MEDIUM': '#f39c12',   # Orange
            'HIGH': '#e74c3c',     # Rouge
            'CRITICAL': '#8b0000'  # Rouge foncé
        }
        return color_map.get(risk_level, '#95a5a6')
    
    # Sinon gradient basé sur score
    if risk_score < 25:
        return '#2ecc71'
    elif risk_score < 50:
        return '#f39c12'
    elif risk_score < 75:
        return '#e74c3c'
    else:
        return '#8b0000'


def display_risk_map(scores_data: pd.DataFrame, height: int = 600) -> None:
    """
    Affiche la carte interactive avec marqueurs colorés selon risque
    
    Args:
        scores_data: DataFrame avec colonnes:
            - code: Code département
            - name: Nom département
            - risk_score: Score 0-100
            - risk_level: Catégorie
            - coverage_rate: Taux couverture
            - urgences_count: Passages urgences
        height: Hauteur carte en pixels
    """
    
    # Créer la carte de base
    m = folium.Map(
        location=[MAP_CONFIG['center_lat'], MAP_CONFIG['center_lon']],
        zoom_start=MAP_CONFIG['zoom'],
        tiles='cartodbpositron'
    )
    
    # Marker cluster optionnel (décommenter si trop de départements)
    # marker_cluster = MarkerCluster().add_to(m)
    
    # Ajouter les marqueurs
    for _, row in scores_data.iterrows():
        code = str(row['code'])
        
        # Récupérer coordonnées (skip si pas disponible)
        coords = DEPT_COORDS.get(code)
        if coords is None:
            continue
        
        # Couleur selon niveau de risque
        color = get_color_for_risk(
            row['risk_score'],
            row.get('risk_level')
        )
        
        # Taille du marqueur proportionnelle au score
        radius = max(8, min(25, row['risk_score'] / 4))
        
        # Popup avec infos détaillées
        popup_html = f"""
        <div style="font-family: Arial; width: 250px;">
            <h4 style="margin: 0 0 10px 0; color: {color};">
                {row.get('name', code)} ({code})
            </h4>
            <table style="width: 100%; font-size: 12px;">
                <tr>
                    <td><b>Score de risque:</b></td>
                    <td style="text-align: right;">{row['risk_score']:.1f}/100</td>
                </tr>
                <tr>
                    <td><b>Niveau:</b></td>
                    <td style="text-align: right; color: {color};">
                        <b>{row.get('risk_level', 'N/A')}</b>
                    </td>
                </tr>
                <tr>
                    <td><b>Couverture:</b></td>
                    <td style="text-align: right;">{row.get('coverage_rate', 0):.1f}%</td>
                </tr>
                <tr>
                    <td><b>Urgences:</b></td>
                    <td style="text-align: right;">{int(row.get('urgences_count', 0)):,}</td>
                </tr>
            </table>
        </div>
        """
        
        # Créer le marqueur
        folium.CircleMarker(
            location=coords,
            radius=radius,
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=2,
            opacity=0.8,
        ).add_to(m)
    
    # Légende
    legend_html = f"""
    <div style="position: fixed; 
                bottom: 50px; left: 50px; 
                background-color: white; 
                border: 2px solid grey; 
                border-radius: 5px; 
                padding: 10px; 
                z-index: 9999;
                font-size: 14px;">
        <h4 style="margin: 0 0 10px 0;">Niveau de Risque</h4>
        <p style="margin: 5px 0;">
            <span style="background-color: #2ecc71; width: 20px; height: 10px; display: inline-block;"></span>
            Faible (0-25)
        </p>
        <p style="margin: 5px 0;">
            <span style="background-color: #f39c12; width: 20px; height: 10px; display: inline-block;"></span>
            Modéré (25-50)
        </p>
        <p style="margin: 5px 0;">
            <span style="background-color: #e74c3c; width: 20px; height: 10px; display: inline-block;"></span>
            Élevé (50-75)
        </p>
        <p style="margin: 5px 0;">
            <span style="background-color: #8b0000; width: 20px; height: 10px; display: inline-block;"></span>
            Critique (75-100)
        </p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Afficher la carte avec streamlit-folium
    st_folium(m, width=None, height=height, returned_objects=[])
