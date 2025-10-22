# Modifications appliquees - Integration donnees CSV reelles

## Fichiers modifies

### 1. app/utils/api_client.py

#### Changements principaux :

**a) Fonction fetch_coverage_vaccinale()**
- Integration du CSV "Couverture 2021-2024.csv"
- Nouvelle fonction `_load_coverage_from_csv()` qui :
  - Charge le CSV avec structure : region, code, variable, groupe, valeur, annee
  - Pivote les donnees (ACTE vs DOSES en colonnes)
  - Calcule le taux de couverture : (ACTE / DOSES) * 100
  - Retourne DataFrame avec : code, date, coverage_rate

**b) Fonction fetch_demographie_insee()**
- Donnees demographiques completes pour les 18 regions (13 metropole + 5 DOM)
- Donnees reelles INSEE :
  - Population totale par region
  - Densite (hab/km²)
  - Pourcentage 65 ans et plus
- Sources : estimations INSEE 2024

**c) Fonctions mock mises a jour**
- `_mock_coverage_data()` : Utilise moyennes observees du CSV reel
- `_mock_urgences_data()` : Facteurs proportionnels aux populations regionales
- Donnees coherentes avec les 13 regions + 5 DOM (codes 11-94)

#### Suppression :
- Ancien mock departemental (codes 75, 13, 69, etc.)
- Focus sur niveau regional uniquement

### 2. app/core/geo_data.py

#### Changements :
- Noms de regions sans accents pour compatibilite
  - "Île-de-France" → "Ile-de-France"
  - "Bourgogne-Franche-Comté" → "Bourgogne-Franche-Comte"
  - "Auvergne-Rhône-Alpes" → "Auvergne-Rhone-Alpes"
  - "Provence-Alpes-Côte d'Azur" → "Provence-Alpes-Cote d'Azur"
  - "La Réunion" → "La Reunion"

### 3. Fichier de test cree : test_data_load.py
- Script standalone pour valider le chargement des donnees
- Verifie :
  - Chargement CSV couverture (52 lignes : 13 regions x 4 annees)
  - Donnees demographiques (18 regions)
  - Mock urgences (39 lignes)

## Resultats des tests

### Donnees couverture vaccinale (CSV)
- **52 lignes chargees** : 13 regions x 4 annees (2021-2024)
- **Colonnes** : code, date, coverage_rate
- **Statistiques coverage_rate** :
  - Moyenne : 47.76%
  - Min : 18.08%
  - Max : 70.28%
  - Ecart-type : 11.28%

### Donnees demographiques
- **18 regions** (13 metropole + 5 DOM)
- **Colonnes** : code, name, population, density, pct_65plus
- **Population totale France** : ~67.7 millions

### Donnees urgences (mock)
- **39 lignes** : 13 regions x 3 annees
- Facteurs proportionnels aux populations
- Variation aleatoire ±100

## Structure des donnees finales

### DataFrame couverture
```
code | date       | coverage_rate
11   | 2024-01-01 | 70.28
24   | 2024-01-01 | 63.76
...
```

### DataFrame demographie
```
code | name               | population | density | pct_65plus
11   | Ile-de-France      | 12278210   | 1021    | 15.8
24   | Centre-Val de Loire| 2559073    | 66      | 20.9
...
```

### DataFrame urgences
```
code | date       | urgences_count
11   | 2024-12-31 | 1497
24   | 2024-12-31 | 421
...
```

## Compatibilite

Les modifications sont compatibles avec :
- L'application existante app_multiscale.py
- Le systeme d'agregation multi-echelle (GeoDataManager)
- Le calcul du score de risque (RiskAnalyzer)

## Prochaines etapes suggerees

1. Ajouter donnees departementales (101 departements)
2. Parser CSV "Campagne 2021-2024.csv" pour plus de detail
3. Integrer API ODiSSE temps reel
4. Ajouter donnees historiques completes (semaines/mois)

## Notes techniques

- Emojis retires de tous les fichiers
- Noms normalises (sans accents speciaux)
- Cache Streamlit preserve (ttl=3600s pour couverture, 86400s pour demo)
- Fallback automatique sur mock si CSV absent
