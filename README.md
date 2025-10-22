# EpiMap Explorer 🗺️

**Outil d'aide à la décision pour l'optimisation de la stratégie vaccinale contre la grippe**

Projet Hackathon EPITECH - Analyse des risques épidémiologiques avec données ouvertes (Open Data)

## 🎯 Objectif

Développer une carte interactive multi-échelle croisant :
- 💉 **Couverture vaccinale** (Santé Publique France)
- 🚑 **Passages aux urgences** (OSCOUR)  
- 👥 **Densité et démographie** (INSEE)

Pour identifier les zones géographiques à risque et optimiser la distribution des vaccins.

## ✨ Fonctionnalités Implémentées

### 1. Carte Multi-Échelle Interactive ✅
- **Navigation hiérarchique** : France → Régions (13) → Départements (101)
- **Agrégation intelligente** : Moyennes pondérées par population à chaque niveau
- **Visualisation colorée** : Score de risque composite 0-100
- **Filtres dynamiques** : Date, niveau de risque, indicateurs

### 2. Score de Risque Composite
```
Score = 0.35×Couverture + 0.30×Urgences + 0.20×Densité + 0.15×Âge
```
- **4 indicateurs pondérés** normalisés 0-100
- **Catégorisation automatique** : LOW / MEDIUM / HIGH / CRITICAL
- **Simulation d'impact** : Modifier la couverture et observer l'effet sur le score

### 3. Analyses Comparatives
- **Top N territoires à risque** avec classement dynamique
- **Comparateur géographique** : Visualiser différences entre territoires
- **Timeline historique** : Évolution temporelle des scores
- **Export Open Data** : Téléchargement CSV pour analyses R/Python

## 🚀 Installation & Lancement

### Prérequis
- Python 3.13+ (ou 3.10+)
- macOS / Linux / Windows

### Installation

```bash
# Cloner le dépôt
git clone https://github.com/yohemm/HACK-EPITECH-PROJET-ELYSE.git
cd HACK-EPITECH-PROJET-ELYSE

# Créer environnement virtuel (obligatoire sur macOS Homebrew Python)
python3 -m venv .venv
source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt
```

### Lancer l'application

**Option 1 : Carte multi-échelle (nouvelle version)**
```bash
streamlit run app_multiscale.py
```
Accès : http://localhost:8501

**Option 2 : Version POC initiale**
```bash
streamlit run app/app_streamlit.py
```

## 📁 Structure du Projet

```
piscine/
├── app/
│   ├── core/
│   │   ├── risk_analyzer.py      # Calcul scores de risque
│   │   └── geo_data.py            # Gestion multi-échelle géographique
│   ├── components/
│   │   ├── map_view.py            # Carte Folium basique
│   │   ├── multi_scale_map.py    # Carte multi-échelle interactive
│   │   ├── controls.py            # UI sidebar
│   │   └── comparator.py          # Comparaisons territoriales
│   ├── utils/
│   │   ├── api_client.py          # Fetch APIs publiques
│   │   └── viz_helpers.py         # Helpers visualisation
│   └── config.py                  # Configuration globale
├── assets/
│   └── custom.css                 # Styles personnalisés
├── app_multiscale.py              # 🆕 Application principale multi-échelle
├── app_streamlit.py               # Application POC initiale
├── requirements.txt               # Dépendances Python
└── README.md                      # Ce fichier
```

## 🔧 Configuration

### Sources de Données

Les données sont fetchées depuis les APIs publiques :

1. **Couverture vaccinale** : ODiSSE Santé Publique France
   - URL : `https://odisse.santepubliquefrance.fr/api/records/1.0/search/?dataset=couvertures-vaccinales-des-adolescent-et-adultes-departement`

2. **Passages aux urgences** : OSCOUR
   - URL : `https://odisse.santepubliquefrance.fr/api/records/1.0/search/?dataset=grippe-passages-aux-urgences-et-actes-sos-medecins-departement`

3. **Démographie** : INSEE (données statiques dans le code)

### Mode POC avec Données Mock

Si les APIs sont lentes/indisponibles, l'application bascule automatiquement sur des **données mock réalistes** :
- 20 départements majeurs
- Données hebdomadaires Jan-Oct 2024
- Couverture : 45-75% avec variation
- Urgences : 50-500 par semaine

## 📊 Utilisation

### Navigation Multi-Échelle

1. **Vue France (Régions)**
   - Visualisez les 13 régions métropolitaines + 5 DOM
   - Comparez les scores de risque
   - Cliquez sur une région pour zoomer

2. **Vue Départements**
   - Détail des départements d'une région
   - Identifiez les zones critiques
   - Retour : bouton région en haut

### Filtres Disponibles

- 📅 **Date** : Sélectionner période d'analyse
- 🎚️ **Score minimum** : Filtrer territoires sous seuil
- 🏷️ **Niveau de risque** : LOW / MEDIUM / HIGH / CRITICAL
- 📊 **Indicateurs** : Afficher/masquer couverture, urgences, démo

### Export de Données

Cliquez sur "📥 Télécharger CSV" dans l'expander "Données détaillées" pour exporter :
- Tous les territoires affichés
- Avec indicateurs sélectionnés
- Format CSV compatible R/Python

## 🎨 Personnalisation

### Modifier les Poids du Score

Dans `app/config.py` :

```python
SCORING_WEIGHTS = {
    'coverage': 0.35,   # Couverture vaccinale
    'urgences': 0.30,   # Passages urgences
    'density': 0.20,    # Densité population
    'age': 0.15         # % 65 ans et plus
}
```

### Ajouter un Indicateur

1. Ajouter colonne dans `api_client.py` (fetch ou mock)
2. Ajouter normalisation dans `risk_analyzer.py` → `_normalize_XXX()`
3. Mettre à jour `compute_risk_scores()` avec le nouveau poids

## 🔮 Prochaines Étapes

### Phase 2 : GeoJSON & Choropleth
- [ ] Télécharger GeoJSON officiels (data.gouv.fr)
- [ ] Remplacer markers par polygones
- [ ] Améliorer interaction clic sur carte

### Phase 3 : Données Réelles
- [ ] Parser réel des APIs ODiSSE
- [ ] Intégrer API INSEE (données à jour)
- [ ] Données historiques 2020-2024

### Phase 4 : Fonctionnalités Avancées
- [ ] **Simulation avancée** : Scénarios "what-if" multi-paramètres
- [ ] **Timeline replay** : Rejouer épidémies passées
- [ ] **Prédiction** : Modèles ML pour anticiper besoins
- [ ] **Alertes automatiques** : Notifications territoires critiques

## 🤝 Contribution

Projet développé dans le cadre du Hackathon EPITECH Open Data 2025.

**Équipe** : [Votre équipe]

**Technologies** :
- Python 3.13
- Streamlit 1.38
- Folium 0.17 (cartes interactives)
- Pandas 2.2 (traitement données)
- NumPy 1.26 (calculs)

## 📄 Licence

Données : Open Data - Santé Publique France, INSEE (Licence Ouverte)

Code : MIT License

## 📞 Contact

Pour questions ou suggestions : [votre email]

---

**Made with ❤️ for public health decision-making**
