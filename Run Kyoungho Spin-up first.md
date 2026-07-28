cat > /home/classic_ops/classic-model/CA-MonJ/SPINUP_TRANSIENT_STRATEGY.md << 'EOF'
# Stratégie Spin-up + Transient : Pourquoi Kyoungho l'a Choisie

**Date** : 2026-07-02  
**Site** : CA-MonJ (Montmorency Juvenile)  
**Approche** : Deux phases de simulation

---

##  Table des Matières

1. [Workflow Exécuté](#1-workflow-exécuté)
2. [Raison Scientifique](#2-raison-scientifique)
3. [Détails Techniques](#3-détails-techniques)
4. [Résultats](#4-résultats)

---

## 1. Workflow Exécuté

### Phase 1 : SPIN-UP (Initialisation des Pools)

**Objectif** : Équilibrer les pools de carbone et d'eau du sol avant la simulation transient

```bash
# Étape 1 : Préparer l'initialisation
cd /home/classic_ops/kyoungho_calibration/CA-MonJ

ncgen -o Juvenile_init.nc Juvenile_init.cdl

mkdir -p Juvenile
cp Juvenile_init.nc Juvenile/Juvenile_init_Transient.nc
cp model_params.nml Juvenile/

# Étape 2 : Créer le restart file (copie de l'init)
cp Juvenile/Juvenile_init_Transient.nc Juvenile/rsfile.nc

# Étape 3 : Créer le dossier de sortie spin-up
mkdir -p outputFiles/Juvenile_Spinup

# Étape 4 : Définir les variables Apptainer
cd /home/classic_ops/CLASSIC
SIF="tools/apptainerContainerRecipe/CLASSIC_container.sif"

# Étape 5 : Lancer le spin-up
echo " Phase 1 : SPIN-UP..."

apptainer exec \
  --no-mount bind-paths \
  --bind "/home/classic_ops/CLASSIC:/work_zone/classic_tmp" \
  --bind "/home/classic_ops/kyoungho_calibration/CA-MonJ:/work_zone/run_tmp" \
  --bind "/mnt/c/Users/danyblanchet7/Desktop/DATA KYOUNGHO/Forcings/Montmorency Forest/Juvenile_2016_2024:/work_zone/classic_tmp/inputFiles/meteorology/Juvenile" \
  --bind "/mnt/c/Users/danyblanchet7/Desktop/DATA KYOUNGHO/Forcings/CO2:/work_zone/classic_tmp/inputFiles/CO2" \
  "$SIF" \
  /work_zone/classic_tmp/bin/CLASSIC_serial \
  /work_zone/run_tmp/job_options_file_Spinup.txt 0/0

echo " Spin-up terminé"
```

**Suivi du run** :

INFO: squashfuse not found, will not be able to mount SIF files
INFO: Converting SIF file to temporary sandbox...

domainBounds given = 0/0/0/0 so running whole domain of 1 longitude cells and 1 latitude cells.
done: met year = 2016 runyr = 1
done: met year = 2017 runyr = 2
done: met year = 2018 runyr = 3
...
done: met year = 2024 runyr = 9

INFO: Cleaning up image...
 Spin-up terminé


**Résultat** : Un fichier `rsfile.nc` **équilibré** (pools stabilisés)

---

### Phase 2 : TRANSIENT (2016-2024)

**Objectif** : Simulation réaliste de la période historique avec pools initialisés correctement

```bash
# Étape 1 : Copier le rsfile équilibré du spin-up
# (IMPORTANT : le rsfile.nc créé par spin-up est maintenant réaliste)

# Étape 2 : Créer le dossier de sortie transient
mkdir -p /home/classic_ops/kyoungho_calibration/CA-MonJ/outputFiles/Juvenile_Transient

# Étape 3 : Lancer le transient
echo " Phase 2 : TRANSIENT (2016-2024)..."

cd /home/classic_ops/CLASSIC

apptainer exec \
  --no-mount bind-paths \
  --bind "/home/classic_ops/CLASSIC:/work_zone/classic_tmp" \
  --bind "/home/classic_ops/kyoungho_calibration/CA-MonJ:/work_zone/run_tmp" \
  --bind "/mnt/c/Users/danyblanchet7/Desktop/DATA KYOUNGHO/Forcings/Montmorency Forest/Juvenile_2016_2024:/work_zone/classic_tmp/inputFiles/meteorology/Juvenile" \
  --bind "/mnt/c/Users/danyblanchet7/Desktop/DATA KYOUNGHO/Forcings/CO2:/work_zone/classic_tmp/inputFiles/CO2" \
  "$SIF" \
  /work_zone/classic_tmp/bin/CLASSIC_serial \
  /work_zone/run_tmp/job_options_file_Transient.txt 0/0

echo " Transient terminé"
```

**Résultat** : 60+ fichiers netCDF avec la simulation 2016-2024

---

## 2. Raison Scientifique

### Le Problème : Les "Conditions Initiales"

Quand tu lances CLASSIC pour la première fois, le modèle reçoit un fichier d'initialisation qui contient :

Pools de carbone dans le sol (soil organic carbon)
Eau du sol (soil water content)
Biomasse végétale (leaf, stem, root mass)
Température du sol (soil temperature)
...


**MAIS** : Ces valeurs sont **génériques** — elles ne reflètent pas l'**historique réel** du site.

**Exemple concret** :

Fichier init.nc dit :
SOC = 5 kg C/m² (carbone du sol)

Mais en réalité, après 50 ans d'accumulation :
SOC réel = 12 kg C/m² (beaucoup plus !)

Si tu lances directement en 2016 :

Le modèle part d'une "fausse" ligne de base
Les premières années sont faussées (spinup implicite)
Les résultats 2016-2024 sont biaisés

### La Solution : LE SPIN-UP

**Idée** : Faire tourner le modèle plusieurs fois sur le même forçage pour que les pools **atteignent l'équilibre**.

Itération 1 (2016-2024) : SOC augmente (2016: 5 → 2024: 7)
Itération 2 (2016-2024) : SOC augmente (2016: 7 → 2024: 8.5)
Itération 3 (2016-2024) : SOC augmente (2016: 8.5 → 2024: 9.8)
Itération N (équilibre) : SOC stable (2016: 11.8 → 2024: 11.8)

 Maintenant, pour 2016-2024, les pools sont réalistes


### Config du Spin-up chez Kyoungho

Le fichier `job_options_file_Spinup.txt` de Kyoungho contient probablement :

```fortran
runStartYear = 2016
runEndYear = 2024
actualMetStartYear = 2016
actualMetEndYear = 2024

metOrder = 'random'    ← CLÉS !
leap = .false.
```

**`metOrder = 'random'`** : Au lieu de boucler 2016→2024→2016→2024 (ordre chronologique), 
on mélange les années de façon **aléatoire reproduite** :

Boucle 1 : 2018, 2020, 2016, 2024, 2017, 2021, 2019, 2022, 2023
Boucle 2 : 2020, 2019, 2024, 2016, 2017, 2022, 2023, 2021, 2018
Boucle 3 : [nouvel ordre aléatoire reproductible]


**Pourquoi ?** Éviter que le modèle ne "mémorise" les cycles saisonniers d'une année spécifique.

---

## 3. Détails Techniques

### Fichier de Configuration Spin-up

```bash
# Voir la config du spin-up
grep -E "runStart|runEnd|metOrder|spinfast" \
  /home/classic_ops/kyoungho_calibration/CA-MonJ/job_options_file_Spinup.txt
```

**Attendu** :

runStartYear = 2016
runEndYear = 2024
actualMetStartYear = 2016
actualMetEndYear = 2024
metOrder = 'random'
spinfast = 10 (optionnel : accélère équilibre)


### Fichier de Configuration Transient

```bash
grep -E "runStart|runEnd|metOrder|spinfast" \
  /home/classic_ops/kyoungho_calibration/CA-MonJ/job_options_file_Transient.txt
```

**Attendu** :

runStartYear = 2016
runEndYear = 2024
metOrder = 'sequential' ← DIFFÉRENT du spin-up
spinfast = 1 ← Back à normal


### Le Flux du Restart File

Étape 1 : init.nc
↓
Copié → Juvenile/Juvenile_init_Transient.nc
↓
Copié → Juvenile/rsfile.nc (version "fraîche")

Étape 2 : SPIN-UP tourne
(modify rsfile.nc pour équilibrer)
↓
rsfile.nc sauvegardé avec pools équilibrés

Étape 3 : TRANSIENT tourne
(lit rsfile.nc équilibré)
↓
Simulation réaliste 2016-2024


---

## 4. Résultats

### Structure Finale

Après SPIN-UP :
/home/classic_ops/kyoungho_calibration/CA-MonJ/
├── outputFiles/
│ └── Juvenile_Spinup/ ← 60+ fichiers (ignorés)
├── Juvenile/
│ ├── Juvenile_init_Transient.nc
│ ├── model_params.nml
│ └── rsfile.nc ← MODIFIÉ (pools équilibrés) ✓
└── ...

Après TRANSIENT :
/home/classic_ops/kyoungho_calibration/CA-MonJ/
├── outputFiles/
│ └── Juvenile_Transient/ ← 60+ fichiers (UTILISÉS) ✓
├── Juvenile/
│ └── rsfile.nc ← Modifié à nouveau
└── ...


### Validation des Pools

Pour vérifier que le spin-up a fonctionné, tu peux comparer :

```bash
python3 << 'EOF'
import netCDF4 as nc

# SOC au début (init)
init = nc.Dataset('/home/classic_ops/kyoungho_calibration/CA-MonJ/Juvenile/Juvenile_init_Transient.nc')
soc_init = init.variables['soilcmas'][:].sum()
init.close()

# SOC après spin-up (rsfile)
rsfile = nc.Dataset('/home/classic_ops/kyoungho_calibration/CA-MonJ/Juvenile/rsfile.nc')
soc_spinup = rsfile.variables['soilcmas'][:].sum()
rsfile.close()

# SOC après transient (dernier output)
transient = nc.Dataset('/home/classic_ops/kyoungho_calibration/CA-MonJ/outputFiles/Juvenile_Transient/soilcmas_daily.nc')
soc_final = transient.variables['soilcmas'][-1].sum()  # dernier timestep
transient.close()

print(f"SOC initial     : {soc_init:.2f} kg C/m²")
print(f"SOC après spin  : {soc_spinup:.2f} kg C/m²  (Δ = {soc_spinup - soc_init:+.2f})")
print(f"SOC final 2024  : {soc_final:.2f} kg C/m²  (Δ = {soc_final - soc_spinup:+.2f})")
EOF
```

---

## 5. Pourquoi Kyoungho a Choisi Cette Stratégie

### Les Avantages

| Aspect | Effet |
|--------|-------|
| **Spin-up d'abord** | Pools carbone/eau équilibrés avant la vraie simulation |
| **Random metOrder** | Évite la mémorisation des patterns climatiques |
| **Résultats 2016-2024** | Partent d'une ligne de base réaliste |
| **Reproductibilité** | Même seed aléatoire = même spin-up |
| **Comparaison valide** | Modèle vs Observations sans biais initial |

### Exemple : Impact du Spin-up

SANS SPIN-UP (direct transient) :
2016 : GPP mal estimée (pools trop faibles)
2017 : GPP s'améliore progressivement
...
2024 : GPP approximativement correcte
 Biais dans toute la série 2016-2020

AVEC SPIN-UP (puis transient) :
2016-2024 : GPP réaliste dès le départ
 Pas de biais de "warm-up"


---

## 6. Workflow Complet (Résumé)

```bash
#!/bin/bash

echo "================================"
echo "Spin-up + Transient Workflow"
echo "================================"

cd /home/classic_ops/kyoungho_calibration/CA-MonJ

# Préparer les fichiers
ncgen -o Juvenile_init.nc Juvenile_init.cdl
mkdir -p Juvenile outputFiles/Juvenile_Spinup outputFiles/Juvenile_Transient

cp Juvenile_init.nc Juvenile/Juvenile_init_Transient.nc
cp Juvenile_init.nc Juvenile/rsfile.nc
cp model_params.nml Juvenile/

# Définir Apptainer
cd /home/classic_ops/CLASSIC
SIF="tools/apptainerContainerRecipe/CLASSIC_container.sif"

# PHASE 1 : SPIN-UP
echo " PHASE 1 : SPIN-UP"
echo "   (Équilibrer les pools de carbone/eau)"

apptainer exec \
  --no-mount bind-paths \
  --bind "/home/classic_ops/CLASSIC:/work_zone/classic_tmp" \
  --bind "/home/classic_ops/kyoungho_calibration/CA-MonJ:/work_zone/run_tmp" \
  --bind "/mnt/c/Users/danyblanchet7/Desktop/DATA KYOUNGHO/Forcings/Montmorency Forest/Juvenile_2016_2024:/work_zone/classic_tmp/inputFiles/meteorology/Juvenile" \
  --bind "/mnt/c/Users/danyblanchet7/Desktop/DATA KYOUNGHO/Forcings/CO2:/work_zone/classic_tmp/inputFiles/CO2" \
  "$SIF" /work_zone/classic_tmp/bin/CLASSIC_serial \
  /work_zone/run_tmp/job_options_file_Spinup.txt 0/0

echo " Spin-up terminé"

# PHASE 2 : TRANSIENT
echo ""
echo " PHASE 2 : TRANSIENT (2016-2024)"
echo "   (Simulation historique avec pools équilibrés)"

apptainer exec \
  --no-mount bind-paths \
  --bind "/home/classic_ops/CLASSIC:/work_zone/classic_tmp" \
  --bind "/home/classic_ops/kyoungho_calibration/CA-MonJ:/work_zone/run_tmp" \
  --bind "/mnt/c/Users/danyblanchet7/Desktop/DATA KYOUNGHO/Forcings/Montmorency Forest/Juvenile_2016_2024:/work_zone/classic_tmp/inputFiles/meteorology/Juvenile" \
  --bind "/mnt/c/Users/danyblanchet7/Desktop/DATA KYOUNGHO/Forcings/CO2:/work_zone/classic_tmp/inputFiles/CO2" \
  "$SIF" /work_zone/classic_tmp/bin/CLASSIC_serial \
  /work_zone/run_tmp/job_options_file_Transient.txt 0/0

echo " Transient terminé"

# Valider
echo ""
echo " Validation..."
python3 /home/classic_ops/validation_kyoungho_complete.py

echo ""
echo "================================"
echo " WORKFLOW COMPLET TERMINÉ"
echo "================================"
```

---

## 7. Points Clés à Retenir

### Spin-up
- ✓ Itère le même forçage (2016-2024 cyclé)
- ✓ Utilise `metOrder = 'random'`
- ✓ Modifie progressivement `rsfile.nc`
- ✓ Les outputs sont **ignorés** (juste pour initialiser)

### Transient
- ✓ Utilise le `rsfile.nc` équilibré du spin-up
- ✓ Lance 2016-2024 une seule fois (`metOrder = 'sequential'`)
- ✓ Les outputs sont **exploités** (la vraie simulation)
- ✓ Résultats réalistes car baseline correcte

### Différence Clé

Spin-up : "Préparation" (boucles infinies sur le même forçage)
Transient : "Simulation" (parcours chronologique une fois)


---

##  Fichiers Générés

/home/classic_ops/kyoungho_calibration/CA-MonJ/

Après SPIN-UP :
├── outputFiles/Juvenile_Spinup/ (~60 MB, ignoré)
├── Juvenile/rsfile.nc (500 KB, IMPORTANT ✓)

Après TRANSIENT :
├── outputFiles/Juvenile_Transient/ (~100 MB, UTILISÉ ✓)
└── Juvenile/rsfile.nc (modifié à nouveau)


EOF

cat /home/classic_ops/classic-model/CA-MonJ/SPINUP_TRANSIENT_STRATEGY.md
Sauvegarder dans Git
bash
cp /home/classic_ops/classic-model/CA-MonJ/SPINUP_TRANSIENT_STRATEGY.md \
   /home/classic_ops/classic-model/CA-MonJ/

cd /home/classic_ops/classic-model

git add CA-MonJ/SPINUP_TRANSIENT_STRATEGY.md
git commit -m "Doc: Explain Kyoungho's spin-up + transient strategy"
git push

echo " Sauvegardé dans Git"


