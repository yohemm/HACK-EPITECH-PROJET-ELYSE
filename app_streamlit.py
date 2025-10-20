
import os
import json
import pandas as pd
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(page_title="Carte Vaccination Grippe – MVP", layout="wide")

REGIONAL_CSV = "iqvia_regional_2024.csv"
NATIONAL_CSV = "iqvia_campagne_2024.csv"
REGIONS_GEOJSON = "regions.geojson"

@st.cache_data
def load_data():
    regional = pd.read_csv(REGIONAL_CSV)
    national = pd.read_csv(NATIONAL_CSV)
    # Normalize columns
    regional.columns = [c.strip() for c in regional.columns]
    national.columns = [c.strip() for c in national.columns]
    # Ensure code is string with 2 digits for regions
    if "code" in regional.columns:
        regional["code"] = regional["code"].astype(str).str.zfill(2)
    # Numeric coercion
    for col in ["ACTE(VGP)", "DOSES(J07E1)", "ratio_actes_sur_doses"]:
        if col in regional.columns:
            regional[col] = pd.to_numeric(regional[col], errors="coerce")
    return regional, national

regional, national = load_data()

# ---------- UI Sidebar ----------
st.sidebar.header("Filtres")
metric = st.sidebar.selectbox(
    "Couche principale",
    [c for c in ["ACTE(VGP)", "DOSES(J07E1)", "ratio_actes_sur_doses"] if c in regional.columns]
)

st.sidebar.markdown("---")
st.sidebar.caption("Astuce : ajoutez un fichier **regions.geojson** (codes INSEE région à 2 chiffres) "
                   "pour activer la choroplèthe. Sinon, un fallback aux centroïdes s'applique.")

# ---------- Header ----------
st.title("Optimisation de la stratégie vaccinale – Carte interactive (MVP)")
col1, col2 = st.columns([2,1], gap="large")

with col2:
    st.subheader("Synthèse nationale")
    # Show latest national snapshot table
    if not national.empty:
        latest_date = pd.to_datetime(national["date"], errors="coerce").max()
        st.write(f"**Dernière date** : {latest_date.date() if pd.notna(latest_date) else 'n/a'}")
        key_vars = national[national["date"] == latest_date.strftime("%Y-%m-%d") if pd.notna(latest_date) else True]
        # Small pivot to display ACTE/DOSES/cibles si existants
        if {"variable","valeur"}.issubset(key_vars.columns):
            pv = key_vars.pivot_table(index="variable", values="valeur", aggfunc="sum")
            st.dataframe(pv)
        else:
            st.dataframe(national.head(20))

# ---------- Map init ----------
with col1:
    st.subheader("Carte")
    m = folium.Map(location=[46.6, 2.4], zoom_start=6, control_scale=True)

    # Try to draw choropleth if geojson exists
    geo_ok = os.path.exists(REGIONS_GEOJSON)
    if geo_ok:
        with open(REGIONS_GEOJSON, "r", encoding="utf-8") as f:
            geo = json.load(f)

        # Build mapping data frame (value per region code)
        data = regional[["code", metric]].copy()
        data = data.dropna(subset=[metric])

        folium.Choropleth(
            geo_data=geo,
            name="Choroplèthe",
            data=data,
            columns=["code", metric],
            key_on="feature.properties.code",
            fill_opacity=0.8,
            line_opacity=0.3,
            legend_name=metric
        ).add_to(m)

        # Optional popups using region names from the CSV if present
        # We'll use simple markers at approximate centroids if present in geo
        try:
            for feat in geo.get("features", []):
                props = feat.get("properties", {})
                code = str(props.get("code", "")).zfill(2)
                name = props.get("nom", props.get("name", code))
                row = regional.loc[regional["code"] == code]
                val = row[metric].values[0] if not row.empty else None
                # Try centroid from geometry if available (not guaranteed)
                # Fallback to the map center
                center = [46.6, 2.4]
                # Popup
                folium.Marker(
                    location=center,
                    tooltip=f"{name} – {metric}: {val:,.0f}" if val is not None else f"{name}",
                    popup=folium.Popup(f"<b>{name}</b><br>{metric}: {val:,.0f}" if val is not None else f"<b>{name}</b>",
                                       max_width=300)
                ).add_to(m)
        except Exception:
            pass

    else:
        # Fallback to centroids for regions (2024 codes; approximate)
        REGION_CENTROIDS = {
            "01": (49.8942, 2.2958),   # Hauts-de-France (approx Amiens)
            "02": (48.6921, 6.1844),   # Grand Est (approx Nancy)
            "03": (47.3220, 5.0415),   # Bourgogne-Franche-Comté (approx Dijon)
            "04": (45.7640, 4.8357),   # Auvergne-Rhône-Alpes (Lyon)
            "06": (44.8378, -0.5792),  # Nouvelle-Aquitaine (Bordeaux)
            "11": (48.8566, 2.3522),   # Île-de-France (Paris)
            "24": (47.9029, 1.9093),   # Centre-Val de Loire (Orléans)
            "27": (48.1173, -1.6778),  # Bretagne (Rennes)
            "28": (48.5734, 7.7521),   # Normandie (approx Rouen/Caen ~ mid)
            "32": (47.2184, -1.5536),  # Pays de la Loire (Nantes)
            "44": (47.2184, -1.5536),  # (legacy) Pays de la Loire
            "52": (47.2184, -1.5536),  # (legacy) Bretagne/Pays de la Loire approx
            "53": (47.2184, -1.5536),  # (legacy) Normandie/PdL approx
            "75": (43.2965, 5.3698),   # Provence-Alpes-Côte d'Azur (Marseille)
            "76": (43.6047, 1.4442),   # Occitanie (Toulouse)
            "84": (45.7640, 4.8357),   # Auvergne-Rhône-Alpes
            "93": (43.2965, 5.3698),   # Provence-Alpes-Côte d'Azur
            "94": (43.2329, -0.0733),  # Corse (approx Corte/Ajaccio midpoint)
        }

        # Merge centroids
        df = regional.copy()
        df["lat"] = df["code"].map(lambda c: REGION_CENTROIDS.get(str(c).zfill(2), (46.6, 2.4))[0])
        df["lon"] = df["code"].map(lambda c: REGION_CENTROIDS.get(str(c).zfill(2), (46.6, 2.4))[1])

        mc = MarkerCluster().add_to(m)
        for _, r in df.iterrows():
            val = r.get(metric, None)
            tooltip = f"{r.get('region', r['code'])} – {metric}: {val:,.0f}" if pd.notna(val) else f"{r.get('region', r['code'])}"
            popup_html = f"""
                <b>{r.get('region', r['code'])}</b><br>
                {metric}: {val:,.0f} <br>
            """
            folium.CircleMarker(
                location=[r["lat"], r["lon"]],
                radius=8 if pd.isna(val) else max(4, min(20, (float(val) ** 0.5) / 25)),
                fill=True,
                tooltip=tooltip,
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(mc)

    # Render map
    st_map = st_folium(m, width=1000, height=700)

st.markdown("---")
st.caption("MVP – ajoutez IAS®, urgences et SOS Médecins pour le scoring de priorité.")
