# Guide Complet : Exécuter CLASSIC avec la Calibration de Kyoungho

## Objectif

Faire tourner le modèle CLASSIC sur le site CA-MonJ (Montmorency Juvenile) en utilisant la paramétrisation calibrée par Kyoungho.

**Date de création** : 2026-07-02
**Auteur** : Dany Blanchet
**Base** : Fichiers de Kyoungho (Juvénile)

---

## 1. Architecture du système

### Fichiers source (dispersés)

```
/home/classic_ops/CLASSIC/
├── bin/CLASSIC_serial          ← Binaire compilé
└── inputFiles/
    ├── meteorology/
    │   └── Juvenile/           ← Données météo (Kyoungho)
    │       ├── metVar_sw.nc
    │       ├── metVar_lw.nc
    │       ├── metVar_pr.nc
    │       ├── metVar_ta.nc
    │       ├── metVar_qa.nc
    │       ├── metVar_wi.nc
    │       └── metVar_ap.nc
    └── CO2/
        └── TRENDY_CO2_1700_2024.nc   ← CO2 global
```

### Répertoire de travail (où on exécute)

```
/home/classic_ops/kyoungho_calibration/CA-MonJ/
├── Juvenile_init.cdl                 ← Template init (de Kyoungho)
├── Juvenile_init.nc                  ← Fichier init généré (GÉNÉRÉ)
├── job_options_file_Spinup.txt       ← Config spin-up (de Kyoungho)
├── job_options_file_Transient.txt    ← Config transient (de Kyoungho)
├── model_params.nml                  ← Paramètres calibrés (de Kyoungho)
├── siteinfo.yaml                     ← Info site (de Kyoungho)
│
├── Juvenile/                         ← Dossier de run
│   ├── Juvenile_init.nc              ← Copie du fichier init
│   ├── model_params.nml              ← Copie des paramètres
│   └── rsfile.nc                     ← Restart (GÉNÉRÉ par CLASSIC)
│
└── outputFiles/
    └── CA-MonJ/
        └── netCDF/                   ← Résultats quotidiens (GÉNÉRÉS)
            ├── gpp_daily.nc
            ├── nep_daily.nc
            ├── hfls_daily.nc
            ├── hfss_daily.nc
            ├── evspsbl_daily.nc
            └── ... (60+ fichiers)
```

### Montage Apptainer

| Container | Host System |
|---|---|
| `/work_zone/classic_tmp` | `/home/classic_ops/CLASSIC` |
| `/work_zone/run_tmp` | `/home/classic_ops/kyoungho_calibration/CA-MonJ` |

---

## 2. Étapes de configuration

### Étape 1 : Vérifier les fichiers météo Kyoungho

```bash
# Vérifier que les données météo existent
ls -lh /home/classic_ops/CLASSIC/inputFiles/meteorology/Juvenile/

# Attendu : 7 fichiers metVar_*.nc

### Étape 2 : Préparer le répertoire de travail

```bash
# Créer la structure
mkdir -p /home/classic_ops/kyoungho_calibration/CA-MonJ/Juvenile
mkdir -p /home/classic_ops/kyoungho_calibration/CA-MonJ/outputFiles/CA-MonJ/netCDF

# Vérifier
tree /home/classic_ops/kyoungho_calibration/CA-MonJ
```

**Output attendu** :

```
kyoungho_calibration/CA-MonJ/
├── Juvenile/
├── outputFiles/
│   └── CA-MonJ/
│       └── netCDF/
└── [autres fichiers de Kyoungho]
```

---

### Étape 3 : Générer init.nc depuis le CDL

**Qu'est-ce que c'est ?**
- CDL = "Climate Description Language" (format texte)
- netCDF = format binaire compressé (ce que CLASSIC lit)
- `ncgen` = outil pour convertir CDL → netCDF

```bash
cd /home/classic_ops/kyoungho_calibration/CA-MonJ

# Générer le fichier netCDF à partir du template CDL
ncgen -o Juvenile_init.nc Juvenile_init.cdl

# Vérifier la génération
ncdump -h Juvenile_init.nc | head -50
```

**À voir** : Liste des variables (ALBS, FCAN, stemmass_s, gleafmas_s, etc.)

**Taille attendue** : ~500 KB à 1 MB

---

### Étape 4 : Copier les fichiers dans le dossier Juvenile

```bash
cd /home/classic_ops/kyoungho_calibration/CA-MonJ

# Copier l'init régénéré
cp Juvenile_init.nc Juvenile/

# Copier les paramètres calibrés
cp model_params.nml Juvenile/

# Vérifier
ls -lh Juvenile/
```

**Expected output** :

```
Juvenile_init.nc (~500 KB)
model_params.nml (~18 KB)
```

---

### Étape 5 : Vérifier le job_options_file_Transient.txt

> **Important** : Ne pas modifier le fichier de Kyoungho !

```bash
# Afficher les chemins clés
grep -E "init_file|rs_file|output_directory|runparams_file|metFile|CO2File" \
  job_options_file_Transient.txt
```

**À voir (exactement)** :

```
init_file = '/work_zone/run_tmp/Juvenile/Juvenile_init_Transient.nc'
runparams_file = '/work_zone/run_tmp/Juvenile/model_params.nml'
output_directory = '/work_zone/run_tmp/outputFiles/...'
metFileFss = '/work_zone/classic_tmp/inputFiles/meteorology/Juvenile/...'
CO2File = '/work_zone/classic_tmp/inputFiles/CO2/...'
```

**Note** : Le fichier init s'appelle `Juvenile_init_Transient.nc` dans le job_options, mais on a généré `Juvenile_init.nc`.
**Solution** : Renommer ou faire lien symbolique

```bash
cd /home/classic_ops/kyoungho_calibration/CA-MonJ/Juvenile

# Option 1 : Copier avec le bon nom
cp Juvenile_init.nc Juvenile_init_Transient.nc

# Option 2 : Lien symbolique
ln -s Juvenile_init.nc Juvenile_init_Transient.nc

# Vérifier
ls -la Juvenile/
```

---

## 3. Lancer le modèle

### Étape 1 : Définir les variables Apptainer

```bash
cd /home/classic_ops/CLASSIC

# Définir les chemins de montage
BIND="--no-mount bind-paths \
  --bind /home/classic_ops/CLASSIC:/work_zone/classic_tmp \
  --bind /home/classic_ops/kyoungho_calibration/CA-MonJ:/work_zone/run_tmp"

SIF="tools/apptainerContainerRecipe/CLASSIC_container.sif"

# Vérifier les variables
echo "BIND = $BIND"
echo "SIF = $SIF"
```

**À voir** : Les deux chemins doivent être affichés sans erreur

---

### Étape 2 : Lancer CLASSIC (transient : 2016-2024)

```bash
cd /home/classic_ops/CLASSIC

echo " Lancement CLASSIC avec Kyoungho..."
apptainer exec $BIND $SIF \
  /work_zone/classic_tmp/bin/CLASSIC_serial \
  /work_zone/run_tmp/job_options_file_Transient.txt 0/0

echo " Run terminé"
```

**Suivi du run** :

```
done: met year = 2016 runyr = 2016
done: met year = 2017 runyr = 2017
...
done: met year = 2024 runyr = 2024
```

Durée attendue : 2-5 minutes selon la machine

---

### Étape 3 : Vérifier les résultats

```bash
# Vérifier que les fichiers ont été générés
ls -lh /home/classic_ops/kyoungho_calibration/CA-MonJ/outputFiles/CA-MonJ/netCDF/ | head

# Compter les fichiers
ls /home/classic_ops/kyoungho_calibration/CA-MonJ/outputFiles/CA-MonJ/netCDF/*.nc | wc -l

# Vérifier la dimension temporelle
python3 << 'EOF'
import netCDF4 as nc
ds = nc.Dataset('/home/classic_ops/kyoungho_calibration/CA-MonJ/outputFiles/CA-MonJ/netCDF/gpp_daily.nc')
print(f"Dimension time : {ds.dimensions['time'].size}")
print(f"Jours par an : {ds.dimensions['time'].size / 9:.1f}")  # 9 ans
ds.close()
EOF
```

**Résultat attendu** :
- ~60 fichiers netCDF générés
- `gpp_daily.nc` : 3288 points temporels (365-366 jours × 9 ans)

---

## 4. Valider les résultats

### Lancer le script de validation

```bash
python3 /home/classic_ops/validation_kyoungho_complete.py
```

### Résultats attendus

| Variable | Critère |
|---|---|
| LE | R² > 0.6 (Kyoungho calibré, donc meilleur que v1) |
| H | R² > 0.5 (Idem) |
| ET | R² > 0.5 |

---

## 5. Sauvegarder dans Git

```bash
# Copier dans le repo
cp -r /home/classic_ops/kyoungho_calibration/CA-MonJ/outputFiles/CA-MonJ/netCDF \
  /home/classic_ops/classic-model/CA-MonJ/validation_results/v2_kyoungho/

# Committer
cd /home/classic_ops/classic-model
git add CA-MonJ/
git commit -m "V2 Kyoungho: Complete run 2016-2024 with transient job_options"
git push
```

---

## 6. Structure finale (résumé)

| Avant run | Après run |
|---|---|
| ✓ `Juvenile_init.cdl` | |
| ✓ `Juvenile_init.nc` (généré) | → ✓ utilisé |
| ✓ `model_params.nml` | → ✓ copié dans `Juvenile/` |
| ✓ `job_options_file_Transient` | → ✓ utilisé (inchangé) |
| | → ✓ `rsfile.nc` (créé) |
| | → ✓ `outputFiles/CA-MonJ/netCDF/*.nc` (60+ fichiers) |

---

## 7. Troubleshooting

| Problème | Cause probable | Solution |
|---|---|---|
| `ncgen : command not found` | netcdf-bin pas installé | `apt-get install netcdf-bin` |
| `netCDF error with tag ncOpen` | Fichier init ne trouve pas rsfile | S'assurer que `rsfile.nc` est dans `Juvenile/` |
| `Cannot find meteorology files` | Données Juvenile pas présentes | Vérifier `/CLASSIC/inputFiles/meteorology/Juvenile/` |
| `Nothing to commit, working tree clean` | Les fichiers n'ont pas changé | Vérifier que les binds Apptainer sont corrects |

---

##  Script d'automatisation (tout-en-un)

Créer le script :

```bash
cat > /home/classic_ops/run_kyoungho_complete.sh << 'EOF'
#!/bin/bash

###############################################################################
# Script Complet : Kyoungho Calibration Setup + Run + Validation
#
# Usage: bash run_kyoungho_complete.sh [spinup|transient]
#        Par défaut : transient
###############################################################################

set -e  # Arrêter à la première erreur

KYOUNGHO_DIR="/home/classic_ops/kyoungho_calibration/CA-MonJ"
CLASSIC_DIR="/home/classic_ops/CLASSIC"
JOB_TYPE="${1:-transient}"  # spinup ou transient

echo "=================================="
echo "Kyoungho CLASSIC Setup + Run"
echo "=================================="
echo "Job type: $JOB_TYPE"
echo ""

# ========== ÉTAPE 1 : VÉRIFIER LES PRÉREQUIS ==========
echo "1️  Vérification des fichiers..."

# Vérifier les données météo Kyoungho
if [ ! -d "$CLASSIC_DIR/inputFiles/meteorology/Juvenile" ]; then
    echo " Erreur : Données météo Juvenile absentes !"
    echo "   Chemin attendu : $CLASSIC_DIR/inputFiles/meteorology/Juvenile/"
    exit 1
fi

meteor_files=$(ls $CLASSIC_DIR/inputFiles/meteorology/Juvenile/metVar*.nc 2>/dev/null | wc -l)
echo "   ✓ Fichiers météo trouvés : $meteor_files/7"

if [ ! -f "$KYOUNGHO_DIR/Juvenile_init.cdl" ]; then
    echo " Erreur : Juvenile_init.cdl absent !"
    exit 1
fi
echo "   ✓ Juvenile_init.cdl trouvé"

# ========== ÉTAPE 2 : GÉNÉRER init.nc ==========
echo ""
echo "2️  Génération de Juvenile_init.nc..."

cd "$KYOUNGHO_DIR"

if ncgen -o Juvenile_init.nc Juvenile_init.cdl; then
    echo "   ✓ Juvenile_init.nc généré avec succès"
else
    echo " Erreur lors de la génération du netCDF"
    exit 1
fi

# Vérifier le fichier généré
if ncdump -h Juvenile_init.nc > /dev/null 2>&1; then
    echo "   ✓ Vérification structure OK"
else
    echo " Fichier init.nc corrompu !"
    exit 1
fi

# ========== ÉTAPE 3 : PRÉPARER DOSSIER JUVENILE ==========
echo ""
echo "3️  Préparation du dossier de run..."

mkdir -p "$KYOUNGHO_DIR/Juvenile"
mkdir -p "$KYOUNGHO_DIR/outputFiles/CA-MonJ/netCDF"

# Copier les fichiers nécessaires
cp Juvenile_init.nc Juvenile/Juvenile_init_Transient.nc
cp model_params.nml Juvenile/

echo "   ✓ Fichiers copiés dans Juvenile/"
ls -lh Juvenile/

# ========== ÉTAPE 4 : LANCER CLASSIC ==========
echo ""
echo "4️  Lancement CLASSIC..."

cd "$CLASSIC_DIR"

BIND="--no-mount bind-paths \
  --bind $CLASSIC_DIR:/work_zone/classic_tmp \
  --bind $KYOUNGHO_DIR:/work_zone/run_tmp"

SIF="tools/apptainerContainerRecipe/CLASSIC_container.sif"

JOB_FILE="/work_zone/run_tmp/job_options_file_${JOB_TYPE^}.txt"

echo "   Job file: $JOB_FILE"
echo "   Lancement..."

if apptainer exec $BIND $SIF \
    /work_zone/classic_tmp/bin/CLASSIC_serial "$JOB_FILE" 0/0; then
    echo "   ✓ CLASSIC run terminé avec succès"
else
    echo " Erreur lors du run CLASSIC"
    exit 1
fi

# ========== ÉTAPE 5 : VÉRIFIER LES RÉSULTATS ==========
echo ""
echo "5️  Vérification des résultats..."

nc_count=$(ls "$KYOUNGHO_DIR/outputFiles/CA-MonJ/netCDF"/*.nc 2>/dev/null | wc -l)
echo "   ✓ Fichiers netCDF générés : $nc_count"

# Vérifier dimension temps
python3 << 'PYEOF'
import netCDF4 as nc
ds = nc.Dataset('/home/classic_ops/kyoungho_calibration/CA-MonJ/outputFiles/CA-MonJ/netCDF/gpp_daily.nc')
n_time = ds.dimensions['time'].size
n_per_year = n_time / 9
print(f"   ✓ Dimension time : {n_time} ({n_per_year:.1f} jours/an)")
ds.close()
PYEOF

# ========== ÉTAPE 6 : VALIDATION ==========
echo ""
echo "6️  Validation des résultats..."

if [ -f "/home/classic_ops/validation_kyoungho_complete.py" ]; then
    python3 /home/classic_ops/validation_kyoungho_complete.py
    echo "   ✓ Validation complète"
else
    echo "   ⚠️  Script de validation absent"
fi

# ========== RÉSUMÉ ==========
echo ""
echo "===================================="
echo " SETUP ET RUN COMPLETS"
echo "===================================="
echo ""
echo "Résultats dans :"
echo "  - Outputs : $KYOUNGHO_DIR/outputFiles/CA-MonJ/netCDF/"
echo "  - Restart : $KYOUNGHO_DIR/Juvenile/rsfile.nc"
echo ""
echo "Prochaines étapes :"
echo "  1. Examiner les graphiques de validation"
echo "  2. Comparer avec v1 (validation_results/)"
echo "  3. Committer à Git si satisfait"
echo ""

EOF

chmod +x /home/classic_ops/run_kyoungho_complete.sh
echo "✓ Script créé : /home/classic_ops/run_kyoungho_complete.sh"
```

---

##  Lancer le workflow complet

```bash
# Version transient (2016-2024)
bash /home/classic_ops/run_kyoungho_complete.sh transient

# Ou version spin-up
bash /home/classic_ops/run_kyoungho_complete.sh spinup
```
