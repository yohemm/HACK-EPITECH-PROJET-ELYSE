import pandas as pd

# --- 1️⃣ Charger les fichiers locaux ---
campagne_path = "Campagne 2024.csv"
couverture_path = "Couverture 2024.csv"
output_path = "iqvia_merged_unifie.csv"

# --- 2️⃣ Fonction utilitaire pour lire avec détection automatique du séparateur ---
def read_csv_smart(path):
    try:
        df = pd.read_csv(path, sep=None, engine="python", encoding="utf-8")
    except Exception:
        df = pd.read_csv(path, sep=";", encoding="utf-8")
    df.columns = [c.strip().lower() for c in df.columns]
    return df

campagne = read_csv_smart(campagne_path)
couverture = read_csv_smart(couverture_path)

# --- 3️⃣ Normalisation des colonnes ---
cols = ["level", "campagne", "date", "region", "code", "variable", "groupe", "valeur", "cible"]

# NATIONAL (Campagne)
campagne_tmp = campagne.copy()
for c in ["campagne", "date", "variable", "valeur", "cible"]:
    if c not in campagne_tmp.columns:
        campagne_tmp[c] = None
campagne_tmp["level"] = "national"
campagne_tmp["region"] = "France"
campagne_tmp["code"] = "FR"
campagne_tmp["groupe"] = ""
campagne_unified = campagne_tmp[cols]

# REGIONAL (Couverture)
cov_tmp = couverture.copy()
for c in ["region", "code", "variable", "groupe", "valeur"]:
    if c not in cov_tmp.columns:
        cov_tmp[c] = None
cov_tmp["level"] = "regional"
cov_tmp["campagne"] = ""
cov_tmp["date"] = ""
cov_tmp["cible"] = ""
couverture_unified = cov_tmp[cols]

# --- 4️⃣ Fusionner les deux fichiers ---
merged = pd.concat([campagne_unified, couverture_unified], ignore_index=True)

# --- 5️⃣ Sauvegarder le fichier fusionné ---
merged.to_csv(output_path, index=False, encoding="utf-8")

print(f"✅ Fichier fusionné sauvegardé : {output_path}")
print(f"Nombre total de lignes : {len(merged)}")
print("Aperçu :")
print(merged.head(10))
