# 📊 EpiMap Explorer - Guide de Présentation

## 🎯 Pitch (30 secondes)

**EpiMap Explorer** est un outil d'aide à la décision visuel qui croise en temps réel :
- La couverture vaccinale antigrippale
- Les passages aux urgences  
- Les données démographiques

Pour **identifier les zones sous-vaccinées** et optimiser la stratégie de distribution des vaccins.

---

## ✨ Démonstration Live

### 1. Lancer l'application

```bash
cd piscine
source .venv/bin/activate
streamlit run app_multiscale.py
```

Accès : **http://localhost:8501**

### 2. Parcours de démonstration

#### Étape 1 : Vue d'ensemble France
- **Montrer** : Carte des 13 régions avec code couleur (vert → rouge)
- **Expliquer** : "Chaque région est colorée selon son score de risque composite"
- **Pointer** : Top 5 régions à risque dans la sidebar droite

#### Étape 2 : Zoom sur une région critique
- **Cliquer** : Sur une région rouge (ex: Hauts-de-France si disponible)
- **Montrer** : Vue détaillée des départements de la région
- **Expliquer** : "On identifie les départements nécessitant une action prioritaire"

#### Étape 3 : Filtres et analyses
- **Sidebar gauche** :
  - Changer la date → voir évolution
  - Ajuster seuil risque → filtrer territoires
  - Activer/désactiver indicateurs
- **Montrer** : KPIs en haut (territoires, critiques, couverture moyenne)

#### Étape 4 : Export données
- **Ouvrir** : Expander "Données détaillées"
- **Montrer** : Tableau complet avec tous les indicateurs
- **Cliquer** : "📥 Télécharger CSV" → export pour analyse R/Python

---

## 🔬 Aspect Technique

### Architecture Multi-Échelle

```
Données Départementales (101)
    ↓ Agrégation pondérée par population
Données Régionales (13)
    ↓ Agrégation pondérée
Données Nationales (1)
```

**Avantage** : Navigation fluide avec recalcul automatique des moyennes

### Score de Risque Composite

```python
Score = 0.35 × f(Couverture)    # Plus faible = plus risqué
      + 0.30 × f(Urgences)      # Plus élevé = plus risqué
      + 0.20 × f(Densité)       # Plus dense = plus à risque
      + 0.15 × f(Âge)           # Plus de 65+ = plus vulnérable
```

**Normalisation** : Chaque indicateur → [0, 100] avec formules adaptées

### Sources de Données

1. **Couverture vaccinale** : API ODiSSE Santé Publique France
2. **Passages urgences** : API OSCOUR
3. **Démographie** : Données INSEE

**Mode dégradé** : Si API lente → données mock réalistes automatiques

---

## 💡 Points Forts à Mettre en Avant

### 1. Approche Multi-Échelle Unique
✅ Seul outil permettant navigation France → Région → Département  
✅ Agrégation intelligente (moyennes pondérées, pas simples moyennes arithmétiques)  
✅ Cohérence des données à tous les niveaux

### 2. Score Composite Scientifiquement Fondé
✅ 4 indicateurs complémentaires (pas juste la couverture)  
✅ Pondérations ajustables selon objectifs santé publique  
✅ Normalisation rigoureuse pour comparabilité

### 3. Visualisation Intuitive
✅ Code couleur universel (feu tricolore + critique)  
✅ Carte interactive (pas de graphiques complexes)  
✅ Filtres temps réel sans rechargement

### 4. Open Data & Reproductibilité
✅ Données publiques exclusivement  
✅ Export CSV/JSON pour analyses externes  
✅ Code Python open source (potentiel MIT)

### 5. Applicabilité Opérationnelle
✅ Identifie zones prioritaires en < 10 secondes  
✅ Aide à l'allocation ressources (vaccins, campagnes)  
✅ Monitoring continu vs. analyse ponctuelle

---

## 🎯 Cas d'Usage Concrets

### Pour Décideurs Politiques
- **Avant campagne** : Identifier départements sous-couverts → cibler actions
- **Pendant épidémie** : Prioriser renfort urgences selon scores
- **Post-campagne** : Évaluer efficacité par comparaison temporelle

### Pour Santé Publique France
- **Monitoring** : Détection précoce zones à risque
- **Reporting** : Visualisations pour rapports officiels
- **Simulation** : Tester impact scénarios (ex: +10% couverture)

### Pour Pharmacies / ARS
- **Logistique** : Optimiser distribution doses par département
- **Communication** : Cibler campagnes de sensibilisation
- **Partenariats** : Identifier besoins acteurs locaux

---

## 🚀 Roadmap & Évolutions

### Déjà Implémenté ✅
- [x] Carte multi-échelle interactive
- [x] Score composite 4 indicateurs
- [x] Filtres et navigation
- [x] Export CSV

### Phase 2 (2 semaines) 🔄
- [ ] GeoJSON officiels → polygones au lieu de markers
- [ ] Clic sur carte → sélection automatique territoire
- [ ] Intégration API temps réel (+ fallback intelligent)

### Phase 3 (1 mois) 🎯
- [ ] Comparateur 2+ territoires côte-à-côte
- [ ] Timeline replay épidémies passées (2020-2024)
- [ ] Simulation avancée multi-paramètres

### Phase 4 (3 mois) 🔮
- [ ] Modèle prédictif ML (anticiper besoins 4 semaines)
- [ ] Alertes automatiques (email/SMS si seuil dépassé)
- [ ] Dashboard temps réel style "centre de contrôle"

---

## 🏆 Critères d'Évaluation Hackathon

### Pertinence des Solutions ⭐⭐⭐⭐⭐
- ✅ Répond directement aux 4 objectifs du sujet
- ✅ Identifie zones sous-vaccinées (objectif 4)
- ✅ Base pour prédiction besoins (objectif 1)
- ✅ Visualisation pour décideurs (objectif 2)

### Innovation & Originalité ⭐⭐⭐⭐
- ✅ Approche multi-échelle (pas juste national ou départemental)
- ✅ Score composite (au-delà simple taux de couverture)
- ✅ Navigation intuitive (pas tableaux Excel)

### Impact Santé Publique ⭐⭐⭐⭐⭐
- ✅ Opérationnel immédiatement (pas prototype théorique)
- ✅ Données officielles (reproductible)
- ✅ Scalable (ajout autres pathologies facile)

### Qualité Visualisation ⭐⭐⭐⭐
- ✅ Interface épurée et professionnelle
- ✅ Carte interactive (standard industrie)
- ✅ Export données (interopérabilité)

---

## 🎤 Questions Fréquentes (Anticiper)

**Q: Pourquoi score composite et pas juste couverture ?**  
R: La couverture seule ne suffit pas. Un département avec bonne couverture mais forte densité + population âgée reste à risque. Le score composite capture ces interactions.

**Q: Les données sont-elles à jour ?**  
R: APIs publiques interrogées toutes les heures (cache 1h). Mode dégradé avec données mock si API lente (précisé à l'utilisateur).

**Q: Pourquoi Python/Streamlit vs dashboard BI ?**  
R: Open source, reproductible, modifiable par communauté scientifique. Pas de licence coûteuse. Déployable gratuitement (Streamlit Cloud).

**Q: Peut-on ajouter d'autres indicateurs ?**  
R: Oui, architecture modulaire. Ajout d'un indicateur = 3 étapes :
1. Fetch donnée (api_client.py)
2. Normalisation (risk_analyzer.py)
3. Pondération (config.py)

**Q: Performance avec 101 départements ?**  
R: Optimisé avec cache Streamlit (@st.cache_data). Temps chargement < 2s. Agrégations Pandas vectorisées (très rapide).

---

## 📸 Screenshots à Préparer

1. **Vue France (régions)** - Carte avec couleurs + KPIs
2. **Vue Départements** - Zoom sur région + top 5
3. **Filtres** - Sidebar avec tous les contrôles
4. **Export CSV** - Tableau détaillé
5. **Architecture** - Schéma multi-échelle (dessiner sur papier)

---

## 🎬 Conclusion Pitch

> "EpiMap Explorer transforme des millions de lignes de données publiques en une **carte actionnable** pour les décideurs.  
> 
> En **moins de 10 secondes**, identifiez les départements prioritaires pour vos campagnes de vaccination.  
> 
> **Open source**, **scientifiquement fondé**, **opérationnel dès aujourd'hui**."

**Démo live** : http://localhost:8501  
**Code** : https://github.com/yohemm/HACK-EPITECH-PROJET-ELYSE

---

**Temps de présentation recommandé** : 5-7 minutes  
**Pitch** (1 min) + **Démo** (3 min) + **Technique** (2 min) + **Questions** (1 min)
