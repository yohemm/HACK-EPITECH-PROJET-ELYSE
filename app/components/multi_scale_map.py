"""
Carte multi-échelle interactive avec zoom progressif
France → Région → Département
"""

import folium
from folium import plugins
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import json
from typing import Optional, Dict, Any

from app.config import MAP_CONFIG
from app.core.geo_data import GeoDataManager


class MultiScaleMap:
    """
    Carte interactive multi-échelle
    Gère la navigation hiérarchique France → Région → Département
    """
    
    def __init__(self, geo_manager: GeoDataManager):
        self.geo_manager = geo_manager
        self.geojson_cache = {}
    
    
    def create_map(
        self,
        data: pd.DataFrame,
        level: str = 'regional',
        selected_region: Optional[str] = None,
        metric_col: str = 'risk_score',
        title: str = "Carte des Risques"
    ) -> folium.Map:
        """
        Crée une carte folium au niveau spécifié
        
        Args:
            data: DataFrame avec colonnes [code, name, metric_col, ...]
            level: 'national', 'regional', 'departmental'
            selected_region: Si departmental, code région
            metric_col: Colonne utilisée pour colorier
            title: Titre de la carte
        
        Returns:
            Carte folium
        """
        # Centrage et zoom selon niveau
        if level == 'national' or level == 'regional':
            center = [46.6, 2.5]
            zoom = 5 if level == 'regional' else 6
        else:  # departmental
            center = self._get_region_center(selected_region)
            zoom = 7
        
        # Créer carte de base
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles='cartodbpositron',
            prefer_canvas=True
        )
        
        # Ajouter choropleth si GeoJSON disponible
        try:
            geojson_data = self._load_geojson(level, selected_region)
            
            if geojson_data and not data.empty:
                self._add_choropleth(
                    m, data, geojson_data, metric_col, level
                )
        except Exception as e:
            st.warning(f"GeoJSON non disponible pour {level}: {e}")
            # Fallback: markers
            self._add_markers(m, data, metric_col)
        
        # Titre
        title_html = f'''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 400px; height: 50px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:18px; font-weight: bold; padding: 10px;">
            {title}
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Légende
        self._add_legend(m, metric_col)
        
        return m
    
    
    def _get_region_center(self, region_code: Optional[str]) -> list:
        """Centre géographique approximatif d'une région"""
        centers = {
            '11': [48.8566, 2.3522],   # IDF
            '24': [47.5, 1.5],          # Centre-VdL
            '27': [47.3, 5.0],          # Bourgogne-FC
            '28': [49.0, 0.2],          # Normandie
            '32': [50.0, 3.0],          # Hauts-de-France
            '44': [48.7, 6.2],          # Grand Est
            '52': [47.5, -1.0],         # Pays de Loire
            '53': [48.2, -2.5],         # Bretagne
            '75': [45.5, 0.5],          # Nouvelle-Aquitaine
            '76': [43.6, 2.0],          # Occitanie
            '84': [45.5, 5.5],          # Auvergne-RA
            '93': [43.9, 6.5],          # PACA
            '94': [42.0, 9.0],          # Corse
        }
        return centers.get(region_code, [46.6, 2.5])
    
    
    def _load_geojson(
        self,
        level: str,
        selected_region: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Charge GeoJSON pour le niveau demandé
        TODO: Télécharger GeoJSON officiels depuis data.gouv.fr
        """
        # Pour l'instant, retourner None (pas de GeoJSON)
        # Dans la prochaine étape, on téléchargera les vrais fichiers
        return None
    
    
    def _add_choropleth(
        self,
        m: folium.Map,
        data: pd.DataFrame,
        geojson: Dict,
        metric_col: str,
        level: str
    ):
        """Ajoute une couche choropleth à la carte"""
        
        # Colormap
        vmin = data[metric_col].min()
        vmax = data[metric_col].max()
        
        colormap = folium.LinearColormap(
            colors=['#2ecc71', '#f39c12', '#e74c3c', '#8b0000'],
            vmin=vmin,
            vmax=vmax,
            caption=metric_col
        )
        
        # Choropleth
        folium.Choropleth(
            geo_data=geojson,
            data=data,
            columns=['code', metric_col],
            key_on='feature.properties.code',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.5,
            legend_name=metric_col,
            highlight=True
        ).add_to(m)
        
        # Tooltips interactifs
        folium.GeoJson(
            geojson,
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': 'transparent',
                'weight': 0
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['name', metric_col],
                aliases=['Territoire:', 'Score:'],
                localize=True
            )
        ).add_to(m)
        
        colormap.add_to(m)
    
    
    def _add_markers(
        self,
        m: folium.Map,
        data: pd.DataFrame,
        metric_col: str
    ):
        """
        Fallback: markers circulaires si pas de GeoJSON
        """
        # Utiliser coordonnées existantes
        from app.components.map_view import DEPT_COORDS, get_color_for_risk
        
        for _, row in data.iterrows():
            code = str(row['code'])
            coords = DEPT_COORDS.get(code)
            
            if coords is None:
                continue
            
            metric_val = row.get(metric_col, 0)
            color = get_color_for_risk(metric_val)
            
            # Popup
            popup_html = f"""
            <div style="font-family: Arial; width: 200px;">
                <h4>{row.get('name', code)}</h4>
                <p><b>{metric_col}:</b> {metric_val:.1f}</p>
                <p><b>Couverture:</b> {row.get('coverage_rate', 0):.1f}%</p>
                <p><b>Urgences:</b> {int(row.get('urgences_count', 0)):,}</p>
            </div>
            """
            
            folium.CircleMarker(
                location=coords,
                radius=max(8, metric_val / 5),
                popup=folium.Popup(popup_html, max_width=250),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)
    
    
    def _add_legend(self, m: folium.Map, metric_col: str):
        """Ajoute légende à la carte"""
        legend_html = f"""
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; 
                    background-color: white; 
                    border: 2px solid grey; 
                    border-radius: 5px; 
                    padding: 10px; 
                    z-index: 9999;
                    font-size: 14px;">
            <h4 style="margin: 0 0 10px 0;">{metric_col}</h4>
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


def render_multiscale_map(
    data: pd.DataFrame,
    geo_manager: GeoDataManager,
    current_level: str = 'regional',
    selected_region: Optional[str] = None
) -> Dict[str, Any]:
    """
    Composant Streamlit pour carte multi-échelle
    
    Returns:
        Dict avec interactions utilisateur (clics, sélections)
    """
    
    # Breadcrumb navigation
    st.markdown("### 🗺️ Navigation")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🇫🇷 France", use_container_width=True):
            st.session_state['map_level'] = 'regional'
            st.session_state['selected_region'] = None
            st.rerun()
    
    with col2:
        if current_level in ['departmental'] and selected_region:
            region_name = geo_manager.region_names.get(selected_region, selected_region)
            if st.button(f"📍 {region_name}", use_container_width=True):
                st.session_state['map_level'] = 'regional'
                st.session_state['selected_region'] = None
                st.rerun()
    
    with col3:
        if current_level == 'departmental':
            st.markdown("**🔍 Départements**")
    
    st.divider()
    
    # Créer carte
    map_obj = MultiScaleMap(geo_manager)
    
    title = "France - Toutes régions"
    if current_level == 'departmental' and selected_region:
        region_name = geo_manager.region_names.get(selected_region, selected_region)
        title = f"{region_name} - Départements"
    
    folium_map = map_obj.create_map(
        data=data,
        level=current_level,
        selected_region=selected_region,
        metric_col='risk_score',
        title=title
    )
    
    # Afficher avec interactions
    map_data = st_folium(
        folium_map,
        width=None,
        height=600,
        returned_objects=["last_object_clicked"]
    )
    
    # Gérer clic sur territoire
    if map_data and map_data.get("last_object_clicked"):
        clicked = map_data["last_object_clicked"]
        # TODO: Extraire code territoire et zoomer
        st.info(f"Clic détecté: {clicked}")
    
    return map_data
