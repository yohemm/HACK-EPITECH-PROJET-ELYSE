"""
Gestion des données géographiques multi-échelles
France → Région → Département
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class GeoLevel:
    """Niveau géographique avec données associées"""
    code: str
    name: str
    level: str  # 'national', 'regional', 'departmental'
    parent_code: Optional[str] = None  # Code région parent pour départements
    

# Mapping complet Département → Région (101 départements métropole + DOM)
DEPT_TO_REGION = {
    # Île-de-France (11)
    '75': '11', '77': '11', '78': '11', '91': '11', '92': '11', '93': '11', '94': '11', '95': '11',
    
    # Centre-Val de Loire (24)
    '18': '24', '28': '24', '36': '24', '37': '24', '41': '24', '45': '24',
    
    # Bourgogne-Franche-Comté (27)
    '21': '27', '25': '27', '39': '27', '58': '27', '70': '27', '71': '27', '89': '27', '90': '27',
    
    # Normandie (28)
    '14': '28', '27': '28', '50': '28', '61': '28', '76': '28',
    
    # Hauts-de-France (32)
    '02': '32', '59': '32', '60': '32', '62': '32', '80': '32',
    
    # Grand Est (44)
    '08': '44', '10': '44', '51': '44', '52': '44', '54': '44', '55': '44', '57': '44', '67': '44', '68': '44', '88': '44',
    
    # Pays de la Loire (52)
    '44': '52', '49': '52', '53': '52', '72': '52', '85': '52',
    
    # Bretagne (53)
    '22': '53', '29': '53', '35': '53', '56': '53',
    
    # Nouvelle-Aquitaine (75)
    '16': '75', '17': '75', '19': '75', '23': '75', '24': '75', '33': '75', '40': '75', '47': '75', '64': '75', '79': '75', '86': '75', '87': '75',
    
    # Occitanie (76)
    '09': '76', '11': '76', '12': '76', '30': '76', '31': '76', '32': '76', '34': '76', '46': '76', '48': '76', '65': '76', '66': '76', '81': '76', '82': '76',
    
    # Auvergne-Rhône-Alpes (84)
    '01': '84', '03': '84', '07': '84', '15': '84', '26': '84', '38': '84', '42': '84', '43': '84', '63': '84', '69': '84', '73': '84', '74': '84',
    
    # Provence-Alpes-Côte d'Azur (93)
    '04': '93', '05': '93', '06': '93', '13': '93', '83': '93', '84': '93',
    
    # Corse (94)
    '2A': '94', '2B': '94',
    
    # DOM (codes région = code département pour simplicité)
    '971': '01', '972': '02', '973': '03', '974': '04', '976': '06',  # Guadeloupe, Martinique, Guyane, Réunion, Mayotte
}


REGION_NAMES = {
    '11': 'Ile-de-France',
    '24': 'Centre-Val de Loire',
    '27': 'Bourgogne-Franche-Comte',
    '28': 'Normandie',
    '32': 'Hauts-de-France',
    '44': 'Grand Est',
    '52': 'Pays de la Loire',
    '53': 'Bretagne',
    '75': 'Nouvelle-Aquitaine',
    '76': 'Occitanie',
    '84': 'Auvergne-Rhone-Alpes',
    '93': 'Provence-Alpes-Cote d\'Azur',
    '94': 'Corse',
    '01': 'Guadeloupe',
    '02': 'Martinique',
    '03': 'Guyane',
    '04': 'La Reunion',
    '06': 'Mayotte',
}


DEPT_NAMES = {
    # Île-de-France
    '75': 'Paris', '77': 'Seine-et-Marne', '78': 'Yvelines', '91': 'Essonne',
    '92': 'Hauts-de-Seine', '93': 'Seine-Saint-Denis', '94': 'Val-de-Marne', '95': "Val-d'Oise",
    
    # Centre-Val de Loire
    '18': 'Cher', '28': 'Eure-et-Loir', '36': 'Indre', '37': 'Indre-et-Loire', '41': 'Loir-et-Cher', '45': 'Loiret',
    
    # Bourgogne-Franche-Comté
    '21': "Côte-d'Or", '25': 'Doubs', '39': 'Jura', '58': 'Nièvre', '70': 'Haute-Saône', '71': 'Saône-et-Loire', '89': 'Yonne', '90': 'Territoire de Belfort',
    
    # Normandie
    '14': 'Calvados', '27': 'Eure', '50': 'Manche', '61': 'Orne', '76': 'Seine-Maritime',
    
    # Hauts-de-France
    '02': 'Aisne', '59': 'Nord', '60': 'Oise', '62': 'Pas-de-Calais', '80': 'Somme',
    
    # Grand Est
    '08': 'Ardennes', '10': 'Aube', '51': 'Marne', '52': 'Haute-Marne', '54': 'Meurthe-et-Moselle',
    '55': 'Meuse', '57': 'Moselle', '67': 'Bas-Rhin', '68': 'Haut-Rhin', '88': 'Vosges',
    
    # Pays de la Loire
    '44': 'Loire-Atlantique', '49': 'Maine-et-Loire', '53': 'Mayenne', '72': 'Sarthe', '85': 'Vendée',
    
    # Bretagne
    '22': "Côtes-d'Armor", '29': 'Finistère', '35': 'Ille-et-Vilaine', '56': 'Morbihan',
    
    # Nouvelle-Aquitaine
    '16': 'Charente', '17': 'Charente-Maritime', '19': 'Corrèze', '23': 'Creuse', '24': 'Dordogne',
    '33': 'Gironde', '40': 'Landes', '47': 'Lot-et-Garonne', '64': 'Pyrénées-Atlantiques',
    '79': 'Deux-Sèvres', '86': 'Vienne', '87': 'Haute-Vienne',
    
    # Occitanie
    '09': 'Ariège', '11': 'Aude', '12': 'Aveyron', '30': 'Gard', '31': 'Haute-Garonne',
    '32': 'Gers', '34': 'Hérault', '46': 'Lot', '48': 'Lozère', '65': 'Hautes-Pyrénées',
    '66': 'Pyrénées-Orientales', '81': 'Tarn', '82': 'Tarn-et-Garonne',
    
    # Auvergne-Rhône-Alpes
    '01': 'Ain', '03': 'Allier', '07': 'Ardèche', '15': 'Cantal', '26': 'Drôme',
    '38': 'Isère', '42': 'Loire', '43': 'Haute-Loire', '63': 'Puy-de-Dôme',
    '69': 'Rhône', '73': 'Savoie', '74': 'Haute-Savoie',
    
    # PACA
    '04': 'Alpes-de-Haute-Provence', '05': 'Hautes-Alpes', '06': 'Alpes-Maritimes',
    '13': 'Bouches-du-Rhône', '83': 'Var', '84': 'Vaucluse',
    
    # Corse
    '2A': 'Corse-du-Sud', '2B': 'Haute-Corse',
    
    # DOM
    '971': 'Guadeloupe', '972': 'Martinique', '973': 'Guyane', '974': 'La Réunion', '976': 'Mayotte',
}


class GeoDataManager:
    """
    Gestionnaire de données géographiques multi-échelles
    Permet navigation France → Région → Département
    """
    
    def __init__(self):
        self.dept_to_region = DEPT_TO_REGION
        self.region_names = REGION_NAMES
        self.dept_names = DEPT_NAMES
    
    
    def get_level_name(self, code: str, level: str) -> str:
        """Retourne le nom d'un territoire"""
        if level == 'regional':
            return self.region_names.get(code, f"Région {code}")
        elif level == 'departmental':
            return self.dept_names.get(code, f"Département {code}")
        return "France"
    
    
    def get_parent_region(self, dept_code: str) -> Optional[str]:
        """Retourne le code région pour un département"""
        return self.dept_to_region.get(dept_code)
    
    
    def get_departments_in_region(self, region_code: str) -> List[str]:
        """Liste des départements d'une région"""
        return [
            dept for dept, reg in self.dept_to_region.items()
            if reg == region_code
        ]
    
    
    def aggregate_to_region(
        self,
        df_dept: pd.DataFrame,
        value_cols: List[str],
        weighted_by: str = 'population'
    ) -> pd.DataFrame:
        """
        Agrège données départementales → régionales
        
        Args:
            df_dept: DataFrame avec colonnes [code, date, ...values..., population]
            value_cols: Colonnes à agréger (ex: ['coverage_rate', 'urgences_count'])
            weighted_by: Colonne pour pondération (ex: 'population')
        
        Returns:
            DataFrame régional avec moyennes pondérées
        """
        # Ajouter code région
        df = df_dept.copy()
        df['region_code'] = df['code'].map(self.dept_to_region)
        
        # Grouper par région et date
        group_cols = ['region_code']
        if 'date' in df.columns:
            group_cols.append('date')
        
        agg_dict = {}
        
        # Calcul moyennes pondérées pour taux/pourcentages
        for col in value_cols:
            if 'rate' in col or 'pct' in col or 'coverage' in col:
                # Moyenne pondérée par population
                if weighted_by in df.columns:
                    df[f'{col}_weighted'] = df[col] * df[weighted_by]
                    agg_dict[f'{col}_weighted'] = 'sum'
                    agg_dict[weighted_by] = 'sum'
            else:
                # Somme pour comptages
                agg_dict[col] = 'sum'
        
        # Agréger
        df_agg = df.groupby(group_cols, as_index=False).agg(agg_dict)
        
        # Recalculer moyennes pondérées
        for col in value_cols:
            if 'rate' in col or 'pct' in col or 'coverage' in col:
                if weighted_by in df.columns:
                    df_agg[col] = df_agg[f'{col}_weighted'] / df_agg[weighted_by]
                    df_agg = df_agg.drop(columns=[f'{col}_weighted'])
        
        # Renommer code
        df_agg = df_agg.rename(columns={'region_code': 'code'})
        
        # Ajouter noms
        df_agg['name'] = df_agg['code'].map(self.region_names)
        
        return df_agg
    
    
    def aggregate_to_national(
        self,
        df_region: pd.DataFrame,
        value_cols: List[str],
        weighted_by: str = 'population'
    ) -> pd.DataFrame:
        """
        Agrège données régionales → nationales
        Même logique que aggregate_to_region
        """
        df = df_region.copy()
        
        group_cols = []
        if 'date' in df.columns:
            group_cols.append('date')
        
        agg_dict = {}
        
        for col in value_cols:
            if 'rate' in col or 'pct' in col or 'coverage' in col:
                if weighted_by in df.columns:
                    df[f'{col}_weighted'] = df[col] * df[weighted_by]
                    agg_dict[f'{col}_weighted'] = 'sum'
                    agg_dict[weighted_by] = 'sum'
            else:
                agg_dict[col] = 'sum'
        
        if not group_cols:
            # Agréger tout
            df_agg = pd.DataFrame([df.agg(agg_dict)])
        else:
            df_agg = df.groupby(group_cols, as_index=False).agg(agg_dict)
        
        # Recalculer moyennes
        for col in value_cols:
            if 'rate' in col or 'pct' in col or 'coverage' in col:
                if weighted_by in df.columns:
                    df_agg[col] = df_agg[f'{col}_weighted'] / df_agg[weighted_by]
                    df_agg = df_agg.drop(columns=[f'{col}_weighted'])
        
        df_agg['code'] = 'FR'
        df_agg['name'] = 'France'
        
        return df_agg
    
    
    def get_hierarchy_data(
        self,
        df_dept: pd.DataFrame,
        value_cols: List[str],
        current_level: str = 'national',
        selected_region: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retourne les données au niveau approprié
        
        Args:
            df_dept: Données départementales de base
            value_cols: Colonnes de valeurs
            current_level: 'national', 'regional', 'departmental'
            selected_region: Si departmental, code de la région à afficher
        
        Returns:
            DataFrame filtré selon le niveau
        """
        if current_level == 'departmental':
            if selected_region:
                # Filtrer départements d'une région
                depts = self.get_departments_in_region(selected_region)
                return df_dept[df_dept['code'].isin(depts)].copy()
            return df_dept  # Tous départements
        
        elif current_level == 'regional':
            # Agréger par région
            return self.aggregate_to_region(df_dept, value_cols)
        
        else:  # national
            # Agréger au niveau national
            return self.aggregate_to_national(
                self.aggregate_to_region(df_dept, value_cols),
                value_cols
            )
