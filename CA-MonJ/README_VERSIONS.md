# CA-MonJ Model Calibration Versions

## V1 - Original Setup (Dany)
- **Status**: Initial run, validation moderate
- **init_file**: CA-MonJ_init.nc (stemmass = 0.106 kgC/m²)
- **Results**:
  - LE: R² = 0.261, Bias = -19.10 W/m²
  - H:  R² = -0.065, Bias = +30.63 W/m²
  - ET: R² = 0.550

## V2 - Kyoungho Calibration
- **Status**: Testing Kyoungho's calibrated parameters
- **Source**: Files from Kyoungho (expert calibration)
- **Key files**:
  - Juvénile_init.cdl (init file template)
  - job_options_file_transient.txt
  - job_options_file_Spinup.txt
  - model_params.nml (calibrated parameters)
- **Expected improvements**: Better LE/H partition, GPP validation



## File Organization
CA-MonJ/
├── init_files/
│ ├── v1_original/ ← Original init.nc
│ └── v2_kyoungho/ ← Kyoungho's init (CDL)
├── job_options/
│ ├── v1_original/ ← Original job_options
│ └── v2_kyoungho/ ← Kyoungho's job_options
├── model_params/
│ ├── v1_original/ ← Original params
│ └── v2_kyoungho/ ← Kyoungho's calibrated params
├── siteinfo/
│ ├── v1_original/
│ └── v2_kyoungho/
└── validation_results/
├── v1_original/ ← V1 validation outputs
└── v2_kyoungho/ ← V2 validation outputs
## How to Switch Versions

### To run V1:
```bash
cd /home/classic_ops/kyoungho_calibration  # or your run directory
cp -r /home/classic_ops/classic-model/CA-MonJ/init_files/v1_original/* .
cp -r /home/classic_ops/classic-model/CA-MonJ/job_options/v1_original/* .
```

### To run V2 (Kyoungho):
```bash
cd /home/classic_ops/kyoungho_calibration
cp /home/classic_ops/classic-model/CA-MonJ/init_files/v2_kyoungho/Juvénile_init.cdl .
ncgen -o Juvénile_init.nc Juvénile_init.cdl
cp /home/classic_ops/classic-model/CA-MonJ/job_options/v2_kyoungho/job_options_*.txt .
cp /home/classic_ops/classic-model/CA-MonJ/model_params/v2_kyoungho/model_params.nml .
```
## Comparison Matrix

| Version | LE R² | H R² | ET R² | Status |
|---------|-------|------|-------|--------|
| V1      | 0.261 | -0.065 | 0.550 | Initial |
| V2      | TBD   | TBD  | TBD   |  Testing |

