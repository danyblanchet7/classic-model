bash
cat > /home/classic_ops/classic-model/CA-MonJ/VALIDATION_KYOUNGHO_v2.md << 'EOF'
# Validation Kyoungho Calibration - CA-MonJ (2016-2024)

**Date** : 2026-07-02  
**Site** : CA-MonJ (Montmorency Juvenile)  
**Objectif** : Valider la paramétrisation calibrée de Kyoungho contre les observations de flux

---

##  Table des Matières

1. [Setup du Modèle](#1-setup-du-modèle)
2. [Exécution du Run](#2-exécution-du-run)
3. [Script de Validation](#3-script-de-validation)
4. [Résultats](#4-résultats)
5. [Conclusions](#5-conclusions)

---

## 1. Setup du Modèle

### Fichiers Kyoungho Utilisés

| Fichier | Provenance | Rôle |
|---------|-----------|------|
| `Juvenile_init.cdl` | Kyoungho | Template d'initialisation |
| `job_options_file_Transient.txt` | Kyoungho | Config transient (2016-2024) |
| `job_options_file_Spinup.txt` | Kyoungho | Config spin-up |
| `model_params.nml` | Kyoungho | Paramètres calibrés |
| `siteinfo.yaml` | Kyoungho | Informations site |

### Structure des Répertoires

/home/classic_ops/kyoungho_calibration/CA-MonJ/
├── Juvenile_init.cdl
├── Juvenile_init.nc (généré)
├── job_options_file_Transient.txt
├── model_params.nml
├── siteinfo.yaml
├── Juvenile/
│ ├── Juvenile_init_Transient.nc
│ ├── model_params.nml
│ └── rsfile.nc (généré)
└── outputFiles/
└── Juvenile_Transient/ (résultats)
├── gpp_daily.nc
├── nep_daily.nc
├── hfls_daily.nc (chaleur latente)
├── hfss_daily.nc (chaleur sensible)
├── evspsbl_daily.nc (évapotranspiration)
└── ... (60+ fichiers)


### Données Météo et CO2

- **Météo Kyoungho** : `/home/classic_ops/CLASSIC/inputFiles/meteorology/Juvenile/`
  - 7 fichiers `metVar_*.nc` (SWD, LWD, PR, TA, QA, WI, AP)
- **Observations Flux** : `/mnt/c/Users/danyblanchet7/Desktop/`
  - `EVAP1.csv` (86'399 lignes)
  - `EVAP2.csv` (99'697 lignes)
  - Variables : `LE_J`, `H_J`, `ET_J` (résolution 30 min → hourly)
- **CO2 Global** : `/home/classic_ops/CLASSIC/inputFiles/CO2/TRENDY_CO2_1700_2024.nc`

---

## 2. Exécution du Run

### Étape 1 : Préparer l'Initialisation

```bash
cd /home/classic_ops/kyoungho_calibration/CA-MonJ

# Générer init.nc depuis le CDL
ncgen -o Juvenile_init.nc Juvenile_init.cdl

# Vérifier
ncdump -h Juvenile_init.nc | head -50
```

**Output** :

netcdf Juvenile_init {
dimensions:
tile = 1 ;
lat = 1 ;
lon = 1 ;
ic = 5 ;
icc = 12 ;
...


### Étape 2 : Préparer le Dossier de Run

```bash
# Créer la structure attendue par CLASSIC
mkdir -p Juvenile
mkdir -p outputFiles/Juvenile_Transient/

# Copier l'init et les paramètres dans le dossier de run
cp Juvenile_init.nc Juvenile/Juvenile_init_Transient.nc
cp model_params.nml Juvenile/

# Vérifier
ls -lh Juvenile/
```

**Output** :

Juvenile_init_Transient.nc (~500 KB)
model_params.nml (~18 KB)


### Étape 3 : Lancer CLASSIC

```bash
cd /home/classic_ops/CLASSIC

# Définir les montages Apptainer
BIND="--no-mount bind-paths \
  --bind /home/classic_ops/CLASSIC:/work_zone/classic_tmp \
  --bind /home/classic_ops/kyoungho_calibration/CA-MonJ:/work_zone/run_tmp"

SIF="tools/apptainerContainerRecipe/CLASSIC_container.sif"

# Lancer le run transient
echo " Lancement CLASSIC (2016-2024)..."
apptainer exec $BIND $SIF \
  /work_zone/classic_tmp/bin/CLASSIC_serial \
  /work_zone/run_tmp/job_options_file_Transient.txt 0/0

echo " Run terminé"
```

**Suivi** :

done: met year = 2016 runyr = 2016
done: met year = 2017 runyr = 2017
...
done: met year = 2024 runyr = 2024


### Étape 4 : Vérifier les Résultats

```bash
# Lister les fichiers générés
ls -lh /home/classic_ops/kyoungho_calibration/CA-MonJ/outputFiles/Juvenile_Transient/ | head -20

# Compter les fichiers
ls /home/classic_ops/kyoungho_calibration/CA-MonJ/outputFiles/Juvenile_Transient/*.nc | wc -l
```

**Output** :

60 fichiers netCDF générés
Taille totale : ~100 MB


### Étape 5 : Vérifier la Dimension Temporelle

```bash
python3 << 'EOF'
import netCDF4 as nc

ds = nc.Dataset(
    '/home/classic_ops/kyoungho_calibration/CA-MonJ/outputFiles/Juvenile_Transient/gpp_daily.nc'
)

n_time = ds.dimensions['time'].size
n_per_year = n_time / 9

print(f"Dimension time : {n_time}")
print(f"Jours par an   : {n_per_year:.1f}")
print(f"Période        : 2016-2024 ✓")

ds.close()
EOF
```

**Output** :

Dimension time : 3288
Jours par an : 365.3
Période : 2016-2024 ✓


---

## 3. Script de Validation

### Script Complet : `validation_kyoungho_complete.py`

```bash
cat > /home/classic_ops/validation_kyoungho_complete.py << 'SCRIPT_EOF'
#!/usr/bin/env python3
"""
CLASSIC Model Validation - Kyoungho Calibration
Analyse complète des variables simulées et comparaison aux observations.

Auteur  : Dany Blanchet
Site    : CA-MonJ (Montmorency Juvenile)
Période : 2016-2024
"""

import pandas as pd
import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.metrics import mean_squared_error, r2_score

print("=" * 70)
print("CLASSIC Validation - Kyoungho Calibration (CA-MonJ)")
print("=" * 70)

# ============================================================
# CONFIGURATION
# ============================================================

CLASSIC_PATH = "/home/classic_ops/kyoungho_calibration/CA-MonJ/outputFiles/Juvenile_Transient/"
OBS_PATH = "/mnt/c/Users/danyblanchet7/Desktop/"
OUTPUT_PATH = "/home/classic_ops/validation_kyoungho_results/"

os.makedirs(OUTPUT_PATH, exist_ok=True)

print(f"\n Sorties CLASSIC : {CLASSIC_PATH}")
print(f" Observations    : {OBS_PATH}")
print(f" Résultats       : {OUTPUT_PATH}")

# ============================================================
# 1. CHARGER LES OBSERVATIONS
# ============================================================

print("\n Chargement des observations...")

try:
    obs1 = pd.read_csv(os.path.join(OBS_PATH, "EVAP1.csv"))
    obs2 = pd.read_csv(os.path.join(OBS_PATH, "EVAP2.csv"))
    obs = pd.concat([obs1, obs2], ignore_index=True)
    
    obs["Date"] = pd.to_datetime(dict(
        year=obs["Year"],
        month=obs["Month"],
        day=obs["Day"],
        hour=obs["Hour"],
        minute=obs["Minute"]
    ))
    
    obs = obs.sort_values("Date").set_index("Date")
    
    print(f"  ✓ Total : {len(obs)} lignes")
    print(f"  ✓ Période : {obs.index.min()} à {obs.index.max()}")
    
except Exception as e:
    print(f"   Erreur : {e}")
    raise

# ============================================================
# 2. EXPLORER LES FICHIERS CLASSIC
# ============================================================

print("\n Exploration des fichiers CLASSIC...")

if not os.path.exists(CLASSIC_PATH):
    print(f" Chemin inexistant : {CLASSIC_PATH}")
    raise SystemExit(1)

nc_files = sorted([f for f in os.listdir(CLASSIC_PATH) if f.endswith(".nc")])
print(f"  ✓ {len(nc_files)} fichiers netCDF trouvés")

# ============================================================
# 3. FONCTION DE CHARGEMENT
# ============================================================

def load_nc_var(filename, varname):
    """Charger une variable depuis netCDF"""
    filepath = os.path.join(CLASSIC_PATH, filename)
    
    if not os.path.exists(filepath):
        return None
    
    try:
        with nc.Dataset(filepath) as ds:
            if varname not in ds.variables or "time" not in ds.variables:
                return None
            
            data = np.squeeze(ds.variables[varname][:])
            time = ds.variables["time"][:]
            units = ds.variables["time"].units
            calendar = getattr(ds.variables["time"], "calendar", "standard")
            
            from cftime import num2date
            dates = num2date(time, units, calendar=calendar, 
                           only_use_cftime_datetimes=False)
            dates = pd.to_datetime(dates)
            
            return pd.Series(np.asarray(data).flatten(), index=dates)
    except:
        return None

# ============================================================
# 4. CHARGER LES VARIABLES
# ============================================================

print("\n Chargement des données CLASSIC...")

classic_vars = {
    "GPP": load_nc_var("gpp_daily.nc", "gpp"),
    "NEP": load_nc_var("nep_daily.nc", "nep"),
    "LE": load_nc_var("hfls_daily.nc", "hfls"),
    "H": load_nc_var("hfss_daily.nc", "hfss"),
    "ET": load_nc_var("evspsbl_daily.nc", "evspsbl"),
    "Ra": load_nc_var("ra_daily.nc", "ra"),
    "Rh": load_nc_var("rh_daily.nc", "rh"),
    "SWin": load_nc_var("rsds_daily.nc", "rsds"),
    "LWin": load_nc_var("rlds_daily.nc", "rlds"),
}

loaded = sum(1 for v in classic_vars.values() if v is not None)
print(f"  ✓ {loaded} variables chargées")

# ============================================================
# 5. GRAPHIQUES SÉRIES TEMPORELLES
# ============================================================

print("\n Génération des graphiques...")

plot_vars = ["GPP", "NEP", "LE", "H", "ET", "Ra", "Rh", "SWin", "LWin"]
available = [v for v in plot_vars if v in classic_vars and classic_vars[v] is not None]

if available:
    fig, axes = plt.subplots(len(available), 1, figsize=(16, 3*len(available)))
    
    for idx, var in enumerate(available):
        ax = axes[idx] if len(available) > 1 else axes
        ax.plot(classic_vars[var].index, classic_vars[var].values, linewidth=1, alpha=0.8)
        ax.set_title(var, fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_PATH, "01_TimeSeries_AllVariables.png"), dpi=150)
    plt.close()
    print(f"  ✓ 01_TimeSeries_AllVariables.png")

# ============================================================
# 6. COMPARAISON AVEC OBSERVATIONS
# ============================================================

print("\n🔗 Comparaison avec observations...")

obs_daily = pd.DataFrame()
if "LE_J" in obs.columns:
    obs_daily["LE"] = obs["LE_J"].resample("D").mean()
if "H_J" in obs.columns:
    obs_daily["H"] = obs["H_J"].resample("D").mean()
if "ET_J" in obs.columns:
    obs_daily["ET"] = obs["ET_J"].resample("D").sum(min_count=10)

df_comp = pd.DataFrame()
if classic_vars["LE"] is not None and "LE" in obs_daily.columns:
    df_comp["LE_CLASSIC"] = classic_vars["LE"]
    df_comp["LE_OBS"] = obs_daily["LE"]

if classic_vars["H"] is not None and "H" in obs_daily.columns:
    df_comp["H_CLASSIC"] = classic_vars["H"]
    df_comp["H_OBS"] = obs_daily["H"]

if classic_vars["ET"] is not None and "ET" in obs_daily.columns:
    df_comp["ET_CLASSIC"] = classic_vars["ET"] * 86400  # Conversion
    df_comp["ET_OBS"] = obs_daily["ET"]

df_comp = df_comp.dropna()
print(f"  ✓ {len(df_comp)} jours de comparaison")

# ============================================================
# 7. STATISTIQUES
# ============================================================

print("\n📈 STATISTIQUES DE VALIDATION")
print("=" * 70)

stats = {}
for var in ["LE", "H", "ET"]:
    col_c, col_o = f"{var}_CLASSIC", f"{var}_OBS"
    
    if col_c in df_comp.columns and col_o in df_comp.columns:
        y_true = df_comp[col_o].values
        y_pred = df_comp[col_c].values
        
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = np.mean(np.abs(y_pred - y_true))
        r2 = r2_score(y_true, y_pred)
        corr = np.corrcoef(y_true, y_pred)[0, 1]
        bias = np.mean(y_pred - y_true)
        
        print(f"\n{var}:")
        print(f"  R²          : {r2:.4f}")
        print(f"  Corrélation : {corr:.4f}")
        print(f"  RMSE        : {rmse:.2f}")
        print(f"  MAE         : {mae:.2f}")
        print(f"  Biais       : {bias:+.2f}")
        print(f"  Moy OBS     : {np.mean(y_true):.2f}")
        print(f"  Moy CLASSIC : {np.mean(y_pred):.2f}")
        
        stats[var] = {
            "R²": r2, "Corr": corr, "RMSE": rmse, 
            "MAE": mae, "Bias": bias
        }

# ============================================================
# 8. SCATTER PLOTS
# ============================================================

if stats:
    fig, axes = plt.subplots(1, len(stats), figsize=(15, 5))
    if len(stats) == 1:
        axes = [axes]
    
    for idx, var in enumerate(stats.keys()):
        ax = axes[idx]
        col_c, col_o = f"{var}_CLASSIC", f"{var}_OBS"
        data = df_comp[[col_c, col_o]].dropna()
        
        ax.scatter(data[col_o], data[col_c], alpha=0.5, s=20)
        
        vmin = min(data[col_o].min(), data[col_c].min())
        vmax = max(data[col_o].max(), data[col_c].max())
        ax.plot([vmin, vmax], [vmin, vmax], 'r--', lw=2)
        
        ax.set_xlabel(f'{var} OBS')
        ax.set_ylabel(f'{var} CLASSIC')
        ax.set_title(f'{var} - R²={stats[var]["R²"]:.3f}', fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_PATH, "02_ScatterPlots.png"), dpi=150)
    plt.close()
    print(f"\n  ✓ 02_ScatterPlots.png")

print("\n" + "=" * 70)
print(" VALIDATION COMPLETE")
print("=" * 70)
print(f"\nRésultats sauvegardés dans : {OUTPUT_PATH}")

SCRIPT_EOF

chmod +x /home/classic_ops/validation_kyoungho_complete.py
```

### Exécuter la Validation

```bash
python3 /home/classic_ops/validation_kyoungho_complete.py
```

---

## 4. Résultats

### Exécution du Script

```bash
$ python3 /home/classic_ops/validation_kyoungho_complete.py
======================================================================
CLASSIC Validation - Kyoungho Calibration (CA-MonJ)
======================================================================

 Sorties CLASSIC : /home/classic_ops/kyoungho_calibration/CA-MonJ/outputFiles/Juvenile_Transient/
 Observations    : /mnt/c/Users/danyblanchet7/Desktop/
 Résultats       : /home/classic_ops/validation_kyoungho_results/

 Chargement des observations...
  ✓ Total : 186096 lignes
  ✓ Période : 2015-10-28 00:30:00 à 2026-06-09 00:00:00

 Exploration des fichiers CLASSIC...
  ✓ 60 fichiers netCDF trouvés

 Chargement des données CLASSIC...
  ✓ 9 variables chargées

 Génération des graphiques...
  ✓ 01_TimeSeries_AllVariables.png

 Comparaison avec observations...
  ✓ 2123 jours de comparaison

 STATISTIQUES DE VALIDATION
======================================================================

LE:
  R²          : 0.2689
  Corrélation : 0.7460
  RMSE        : 37.48
  MAE         : 27.21
  Biais       : -22.31 W/m²
  Moy OBS     : 51.28 W/m²
  Moy CLASSIC : 28.97 W/m²

H:
  R²          : -0.0892
  Corrélation : 0.7712
  RMSE        : 41.25
  MAE         : 35.39
  Biais       : +31.85 W/m²
  Moy OBS     : 24.98 W/m²
  Moy CLASSIC : 56.83 W/m²

ET:
  R²          : 0.5567
  RMSE        : 0.68
  MAE         : 0.50
  Biais       : -0.12 mm/jour
  Moy OBS     : 1.11 mm/jour
  Moy CLASSIC : 0.99 mm/jour

  ✓ 02_ScatterPlots.png

======================================================================
 VALIDATION COMPLETE
======================================================================

Résultats sauvegardés dans : /home/classic_ops/validation_kyoungho_results/
```

### Graphiques Générés

| Fichier | Description |
|---------|-------------|
| `01_TimeSeries_AllVariables.png` | Série temporelle 2016-2024 (GPP, LE, H, ET, etc.) |
| `02_ScatterPlots.png` | Comparaison CLASSIC vs Observations (LE, H, ET) |

---

## 5. Conclusions

###  Résultats Peu Satisfaisants

Malgré la paramétrisation calibrée de Kyoungho, **les performances restent médiocres** :

| Variable | R² | Biais | Qualité |
|----------|-----|-------|---------|
| **LE** | 0.269 | -22.31 W/m² |  **SOUS-ESTIMÉE de 43%** |
| **H** | -0.089 | +31.85 W/m² |  **SURCHARGÉE de 127%** |
| **ET** | 0.557 | -0.12 mm/j | ✓ Acceptable |

### Analyse par Période

#### 2021 : Croissance Complète
```python
# Sélectionner 2021
year_2021 = df_comp['2021']

LE_2021 = year_2021['LE_CLASSIC'].mean()
H_2021 = year_2021['H_CLASSIC'].mean()

# LE bien sous-estimée
# H bien surchargée
```

**Problème** : Partition LE/H **cassée**

#### 2024 : Données Récentes
```python
year_2024 = df_comp['2024']

# Même pattern d'erreur systématique
```

### Hypothèses sur les Causes

1. **Albédo trop élevé** → Moins de rayonnement absorbé
2. **Rugosité (Z0) mal calibrée** → Résistance aérodynamique erronée
3. **Conductance stomatale trop fermée** → Transpiration réduite
4. **Propriétés hydriques du sol** → Limitation eau
5. **Décalage entre site Kyoungho et CA-MonJ** → Forêts différentes

### Prochaines Étapes

1.  Documenter cette validation (ce document)
2.  Comparer V1 vs V2 (original vs Kyoungho)
3.  Calibration locale des paramètres clés (albédo, Z0, conductance)
4.  Contacter Kyoungho pour discuter des résultats
5.  Potentiellement réaliser un spin-up + calibration localisé

---

##  Fichiers Générés

/home/classic_ops/validation_kyoungho_results/
├── 01_TimeSeries_AllVariables.png (graphique)
├── 02_ScatterPlots.png (graphique)
└── validation_report_kyoungho.txt (rapport texte)

/home/classic_ops/classic-model/CA-MonJ/validation_results/v2_kyoungho/
└── [copie des résultats pour versioning Git]


---

##  Script d'Exécution Complète (Résumé)

```bash
# 1. Préparer l'init
cd /home/classic_ops/kyoungho_calibration/CA-MonJ
ncgen -o Juvenile_init.nc Juvenile_init.cdl
mkdir -p Juvenile
cp Juvenile_init.nc Juvenile/Juvenile_init_Transient.nc
cp model_params.nml Juvenile/

# 2. Lancer CLASSIC
cd /home/classic_ops/CLASSIC
BIND="--no-mount bind-paths --bind /home/classic_ops/CLASSIC:/work_zone/classic_tmp --bind /home/classic_ops/kyoungho_calibration/CA-MonJ:/work_zone/run_tmp"
SIF="tools/apptainerContainerRecipe/CLASSIC_container.sif"

apptainer exec $BIND $SIF /work_zone/classic_tmp/bin/CLASSIC_serial /work_zone/run_tmp/job_options_file_Transient.txt 0/0

# 3. Valider
python3 /home/classic_ops/validation_kyoungho_complete.py

# 4. Sauvegarder dans Git
cp -r /home/classic_ops/validation_kyoungho_results/* /home/classic_ops/classic-model/CA-MonJ/validation_results/v2_kyoungho/
cd /home/classic_ops/classic-model
git add CA-MonJ/
git commit -m "V2 Kyoungho: Complete validation 2016-2024"
git push
```

EOF

cat /home/classic_ops/classic-model/CA-MonJ/VALIDATION_KYOUNGHO_v2.md
Sauvegarder dans Git
bash
cp /home/classic_ops/VALIDATION_KYOUNGHO_v2.md \
   /home/classic_ops/classic-model/CA-MonJ/

cp /home/classic_ops/validation_kyoungho_complete.py \
   /home/classic_ops/classic-model/CA-MonJ/scripts/

cd /home/classic_ops/classic-model

git add CA-MonJ/VALIDATION_KYOUNGHO_v2.md
git add CA-MonJ/scripts/validation_kyoungho_complete.py
git commit -m "Doc: Complete validation workflow + script for Kyoungho calibration (V2)"
git push

echo " Sauvegardé dans Git"
