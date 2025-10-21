import os
from typing import Dict, Tuple, Optional

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium


# ----------------------------
# App config
# ----------------------------
st.set_page_config(page_title="Accès aux soins - Carte vaccinale", layout="wide")


# ----------------------------
# Data loading / preparation
# ----------------------------
def _default_csv_path() -> Optional[str]:
	"""Return a default CSV path present in the workspace, or None."""
	candidates = [
		"Couverture 2021-2024.csv"
	]
	for c in candidates:
		if os.path.exists(c):
			return c
	return None


def load_data(file) -> pd.DataFrame:
	"""Load CSV into a dataframe with expected columns.

	Expected columns: region, code, variable, groupe, valeur
	variable in {"ACTE(VGP)", "DOSES(J07E1)"}
	groupe in {"65 ans et plus", "moins de 65 ans"}
	
	c'est quoi le besoin
	la cible
	c'est quoi la suite
	Juste vraie et juste 
	tout le monde debout lors de la presentation
	
	"""
	df = pd.read_csv(file)
	# Clean column names if needed
	df.columns = [c.strip().lower() for c in df.columns]
	# Standardize expected column names
	rename_map = {
		"région": "region",
		"code région": "code",
		"valeur ": "valeur",
	}
	df = df.rename(columns=rename_map)

	# Ensure numeric type for values
	if "valeur" in df.columns:
		df["valeur"] = pd.to_numeric(df["valeur"], errors="coerce")

	# Strip spaces/casing for consistency
	for col in ["region", "variable", "groupe"]:
		if col in df.columns:
			df[col] = df[col].astype(str).str.strip()

	# Keep only necessary columns if extras exist
	expected = ["region", "code", "variable", "groupe", "valeur"]
	df = df[[c for c in expected if c in df.columns]]
	return df


def prepare_metrics(df: pd.DataFrame) -> pd.DataFrame:
	"""Pivot data to compute uptake ratios and deficits by age group.

	Returns a dataframe indexed by (region, code) with columns:
	- acte_65p, doses_65p, ratio_65p, deficit_65p
	- acte_m65, doses_m65, ratio_m65, deficit_m65
	"""
	if df.empty:
		return df

	pivot = (
		df.pivot_table(
			index=["region", "code"],
			columns=["variable", "groupe"],
			values="valeur",
			aggfunc="sum",
		)
		.fillna(0)
	)

	# Helper to fetch safely
	def get_col(var: str, grp: str) -> pd.Series:
		if (var, grp) in pivot.columns:
			return pivot[(var, grp)].astype(float)
		return pd.Series(0.0, index=pivot.index)

	acte_65 = get_col("ACTE(VGP)", "65 ans et plus")
	doses_65 = get_col("DOSES(J07E1)", "65 ans et plus")
	acte_m65 = get_col("ACTE(VGP)", "moins de 65 ans")
	doses_m65 = get_col("DOSES(J07E1)", "moins de 65 ans")

	# Compute ratios (acts/doses); if doses==0 -> NaN to avoid misleading 0
	ratio_65 = acte_65.div(doses_65).where(doses_65 > 0)
	ratio_m65 = acte_m65.div(doses_m65).where(doses_m65 > 0)

	out = pd.DataFrame(
		{
			"acte_65p": acte_65,
			"doses_65p": doses_65,
			"ratio_65p": ratio_65,
			"deficit_65p": 1 - ratio_65,
			"acte_m65": acte_m65,
			"doses_m65": doses_m65,
			"ratio_m65": ratio_m65,
			"deficit_m65": 1 - ratio_m65,
		}
	)
	out.index = out.index.set_names(["region", "code"])
	return out.reset_index()


# ----------------------------
# Geocoding for French regions (centroids, approximate)
# ----------------------------
REGION_CENTROIDS: Dict[str, Tuple[float, float]] = {
	# code -> (lat, lon)
	"11": (48.8566, 2.3522),  # Île-de-France (Paris)
	"24": (47.7516, 1.6751),  # Centre-Val de Loire
	"27": (47.2805, 5.9990),  # Bourgogne-Franche-Comté
	"28": (49.1829, 0.3707),  # Normandie (Caen)
	"32": (50.4800, 2.7930),  # Hauts-de-France
	"44": (48.6990, 6.1870),  # Grand Est (Metz)
	"52": (47.2184, -1.5536), # Pays de la Loire (Nantes)
	"53": (48.1173, -1.6778), # Bretagne (Rennes)
	"75": (44.8378, -0.5792), # Nouvelle-Aquitaine (Bordeaux)
	"76": (43.6045, 1.4442),  # Occitanie (Toulouse)
	"84": (45.7640, 4.8357),  # Auvergne-Rhône-Alpes (Lyon)
	"93": (43.2965, 5.3698),  # Provence-Alpes-Côte d'Azur (Marseille)
	"94": (41.9192, 8.7386),  # Corse (Ajaccio)
	# Overseas (optional)
	"01": (16.2650, -61.5510),  # Guadeloupe
	"02": (14.6415, -61.0242),  # Martinique
	"03": (4.9224, -52.3135),   # Guyane
	"04": (-21.1151, 55.5364),  # La Réunion
	"06": (-12.8275, 45.1662),  # Mayotte
}


def latlon_for_code(code: str) -> Optional[Tuple[float, float]]:
	return REGION_CENTROIDS.get(str(code))


# ----------------------------
# UI + Map
# ----------------------------
st.title("Accès aux soins – Repérage des zones à faible uptake vaccinal")
st.caption(
	"Objectif: Identifier les régions où l'uptake (actes/doses) est faible pour orienter des actions ciblées."
)

with st.sidebar:
	st.header("Données")
	uploader = st.file_uploader(
		"Importer un CSV (colonnes: region, code, variable, groupe, valeur)", type=["csv"]
	)

	default_path = _default_csv_path()
	if default_path:
		st.markdown(f"Fichier par défaut détecté: `{default_path}`")

	st.divider()
	st.header("Paramètres")
	age_group = st.selectbox(
		"Groupe d'âge",
		options=["65 ans et plus", "moins de 65 ans"],
		index=0,
	)
	threshold = st.slider(
		"Seuil d'alerte uptake (actes/doses)", min_value=0.0, max_value=1.0, value=0.70, step=0.05
	)
	st.caption(
		"Régions avec uptake < seuil seront marquées en rouge (priorité). Orange si proche du seuil."
	)


# Load data from upload or default
if uploader is not None:
	df_raw = load_data(uploader)
elif default_path is not None:
	df_raw = load_data(default_path)
else:
	df_raw = pd.DataFrame(columns=["region", "code", "variable", "groupe", "valeur"])  # empty


if df_raw.empty:
	st.warning(
		"Aucun fichier CSV trouvé. Importez un fichier via la barre latérale pour commencer."
	)
	st.stop()


df_metrics = prepare_metrics(df_raw)

# Choose columns by age group
if age_group == "65 ans et plus":
	ratio_col, deficit_col, a_col, d_col = "ratio_65p", "deficit_65p", "acte_65p", "doses_65p"
else:
	ratio_col, deficit_col, a_col, d_col = "ratio_m65", "deficit_m65", "acte_m65", "doses_m65"


# Summary KPIs
valid = df_metrics[ratio_col].notna()
nb_regions = int(valid.sum())
nb_flagged = int((df_metrics[ratio_col] < threshold).sum())
avg_ratio = df_metrics.loc[valid, ratio_col].mean() if nb_regions else float("nan")

col1, col2, col3 = st.columns(3)
col1.metric("Régions (avec données)", nb_regions)
col2.metric("Régions sous le seuil", nb_flagged)
col3.metric("Uptake moyen", f"{avg_ratio:.2f}" if pd.notna(avg_ratio) else "–")


# Top regions with highest deficit (largest 1 - ratio)
top_n = (
	df_metrics[["region", "code", ratio_col, deficit_col, a_col, d_col]]
	.sort_values(by=ratio_col, ascending=True)
	.head(5)
)
with st.expander("Top 5 régions à surveiller (uptake le plus faible)"):
	st.dataframe(
		top_n.rename(
			columns={
				ratio_col: "uptake",
				deficit_col: "déficit",
				a_col: "actes",
				d_col: "doses",
			}
		),
		use_container_width=True,
	)


# Map rendering
center = [46.6, 2.5]
zoom_start = 5
fmap = folium.Map(location=center, zoom_start=zoom_start, tiles="cartodbpositron")

for _, row in df_metrics.iterrows():
	ratio = row.get(ratio_col)
	if pd.isna(ratio):
		continue

	code = str(row.get("code"))
	latlon = latlon_for_code(code)
	if not latlon:
		continue  # skip if we don't know the centroid

	# Color logic
	if ratio < threshold:
		color = "#d73027"  # red
	elif ratio < threshold + 0.1:
		color = "#fc8d59"  # orange
	else:
		color = "#1a9850"  # green

	radius = max(6.0, 6 + 25 * (1 - min(1.0, max(0.0, float(ratio)))))

	popup_html = f"""
		<b>{row['region']}</b> (code {code})<br/>
		Uptake ({age_group}): <b>{ratio:.2f}</b><br/>
		Actes: {int(row.get(a_col, 0)):,} | Doses: {int(row.get(d_col, 0)):,}
	"""
	folium.CircleMarker(
		location=latlon,
		radius=radius,
		color=color,
		fill=True,
		fill_opacity=0.7,
		popup=folium.Popup(popup_html, max_width=300),
	).add_to(fmap)


# Legend (custom HTML)
legend_html = f"""
 <div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999; background: white; padding: 10px 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 13px;">
   <div style="font-weight:600; margin-bottom:6px;">Légende – Uptake (actes/doses)</div>
   <div><span style="display:inline-block;width:12px;height:12px;background:#d73027;margin-right:6px;"></span>< {threshold:.2f} (priorité)</div>
   <div><span style="display:inline-block;width:12px;height:12px;background:#fc8d59;margin-right:6px;"></span>{threshold:.2f} – {min(1.0, threshold+0.1):.2f}</div>
   <div><span style="display:inline-block;width:12px;height:12px;background:#1a9850;margin-right:6px;"></span>≥ {min(1.0, threshold+0.1):.2f}</div>
   <div style="margin-top:6px;color:#666;">Taille ∝ déficit (1 - uptake)</div>
 </div>
"""

fmap.get_root().html.add_child(folium.Element(legend_html))

st_data = st_folium(fmap, width=None, height=600)


st.markdown(
	"""
	Notes et hypothèses:
	- Sans dénominateur population (par ex. nombre de personnes 65+), on utilise ici un proxy d'uptake = actes/doses.
	- Pour une analyse de couverture réelle, combinez avec les jeux 'Couvertures vaccinales' (ODiSSE) et les populations INSEE.
	- Vous pouvez remplacer le CSV via l'upload pour intégrer des données plus complètes (département, région, national).
	"""
)
