
# Carte Vaccination Grippe – MVP (Streamlit + Folium)

## Prérequis
- Python 3.9+
- `pip install streamlit folium streamlit-folium pandas`

## Fichiers attendus
- `iqvia_regional_2024.csv` (fourni)
- `iqvia_campagne_2024.csv` (fourni)
- `regions.geojson` (optionnel, pour activer la choroplèthe). Si absent, l'app utilise des centroïdes régionaux par défaut.

## Lancer l'application
```bash
streamlit run app_streamlit.py
```

## Personnalisation
- Remplacez `regions.geojson` par un GeoJSON de régions françaises avec une propriété `code` (INSEE à 2 chiffres) et idéalement `nom`.
- Ajoutez vos autres couches (IAS®, urgences, SOS Médecins) et un score de priorité.
