# Guide Utilisation - Donnees CSV Reelles

## Apercu

L'application utilise maintenant les vraies donnees du fichier `Couverture 2021-2024.csv` qui contient :
- 13 regions metropolitaines
- 4 annees de donnees (2021-2024)
- Actes de vaccination (VGP) et doses distribuees (J07E1)
- Deux groupes d'age : "65 ans et plus" et "moins de 65 ans"

## Structure du CSV source

```csv
region,code,variable,groupe,valeur,annee
11 - ILE-DE-France,11,ACTE(VGP),65 ans et plus,3930,2024
11 - ILE-DE-France,11,DOSES(J07E1),65 ans et plus,5433,2024
```

### Colonnes :
- **region** : Nom de la region (non utilise, juste informatif)
- **code** : Code INSEE region (ex: 11 pour Ile-de-France)
- **variable** : ACTE(VGP) ou DOSES(J07E1)
- **groupe** : "65 ans et plus" ou "moins de 65 ans"
- **valeur** : Nombre (pour 1000 personnes)
- **annee** : 2021, 2022, 2023 ou 2024

## Calcul du taux de couverture

Le taux de couverture est calcule comme suit :

```python
taux_couverture = (ACTE / DOSES) * 100
```

**Interpretation** :
- DOSES = doses distribuees en pharmacie
- ACTE = actes de vaccination realises
- Ratio = efficacite de conversion doses → vaccinations

**Exemple** :
- Ile-de-France 2024, 65+
  - ACTE = 3930 (pour 1000)
  - DOSES = 5433 (pour 1000)
  - Taux = (3930 / 5433) * 100 = 72.3%

## Donnees disponibles par region

### Regions avec meilleur taux de couverture (2024)
1. Ile-de-France (11) : 70.3%
2. Normandie (28) : 65.7%
3. Centre-Val de Loire (24) : 63.8%
4. Bretagne (53) : 61.5%
5. Pays de la Loire (52) : 62.2%

### Regions avec taux de couverture plus faible (2024)
1. Corse (94) : 34.4%
2. Hauts-de-France (32) : 51.8%
3. Bourgogne-Franche-Comte (27) : 56.6%

## Evolution temporelle

Le CSV contient 4 annees de donnees permettant d'observer :
- Tendances annuelles
- Amelioration/degradation par region
- Impact des campagnes de vaccination

**Exemple Ile-de-France** :
- 2021 : 48.8%
- 2022 : 58.4%
- 2023 : 64.1%
- 2024 : 70.3%
→ **Progression constante**

## Utilisation dans l'application

### 1. Chargement automatique

L'application charge automatiquement le CSV si present :

```python
from app.utils.api_client import APIClient

df_coverage = APIClient.fetch_coverage_vaccinale()
# Retourne : code | date | coverage_rate
```

### 2. Agregation par groupe d'age

Le CSV contient deux groupes. Par defaut, l'application calcule la moyenne.

Pour analyser par groupe separement :

```python
# Modifier _load_coverage_from_csv() pour ne pas agréger
# Ou filtrer après chargement
df[df['groupe'] == '65 ans et plus']
```

### 3. Integration avec GeoDataManager

Les donnees sont compatibles avec le systeme multi-echelle :

```python
from app.core.geo_data import GeoDataManager

geo = GeoDataManager()

# Les codes region (11, 24, 27...) matchent parfaitement
# Pas besoin de conversion
```

## Donnees complementaires

### Demographie (fetch_demographie_insee)
Fournit pour chaque region :
- Population totale
- Densite (hab/km²)
- Pourcentage 65 ans et plus

### Urgences (fetch_urgences)
Donnees mock actuellement, a remplacer par :
- CSV "Campagne 2021-2024.csv" (si disponible)
- API ODiSSE OSCOUR temps reel

## Limitations actuelles

1. **Niveau regional uniquement**
   - Pas de donnees departementales dans ce CSV
   - Pour details : utiliser API ODiSSE departementale

2. **Frequence annuelle**
   - Donnees annuelles (2021-2024)
   - Pour suivi hebdo/mensuel : API temps reel necessaire

3. **Pas de donnees DOM dans le CSV**
   - Seules 13 regions metropolitaines
   - DOM (971-976) utilisent donnees mock

## Prochaines ameliorations

1. **Parser "Campagne 2021-2024.csv"** pour plus de detail
2. **Integrer API ODiSSE** pour donnees temps reel
3. **Ajouter niveau departemental** (101 departements)
4. **Donnees hebdomadaires** pour suivi epidemiologique

## Verification des donnees

Pour verifier le bon chargement :

```bash
cd /Users/kevinbiantuadi/Downloads/my_projects/epitech_projects/piscine
source .venv/bin/activate
python test_data_load.py
```

Sortie attendue :
- 52 lignes chargees (13 regions x 4 annees)
- Coverage_rate entre 18% et 70%
- 18 regions demographiques
