# Generate, compile, run and score the COMSOL cross-validation for every
# menu design. Requires: university VPN up (license server), COMSOL 6.4
# tree on the Desktop. Run from _CURRENT\:
#     powershell -File drone_20m\comsol_run_all.ps1
$ErrorActionPreference = "Continue"
$bin = "C:\Users\ASUS\OneDrive\Desktop\COMSOL64\Multiphysics\bin\win64"
$py = "..\.venv\Scripts\python.exe"
$jdir = "drone_20m\designs\comsol\java"

$designs = @(
  "D190_19m_2inch", "D190_26m_trigas", "D160_27m", "D180_24m_H2",
  "D180_15m_sparse", "D130_9m_halfinch", "D190_29m_max",
  "D150_14cm_flight", "D180_22m")

foreach ($d in $designs) {
  Write-Output "==== $d ===="
  & $py drone_20m\comsol_gen.py --design $d
  if ($LASTEXITCODE -ne 0) { Write-Output "GEN FAILED: $d"; continue }
  & "$bin\comsolcompile.exe" "$PWD\$jdir\m_$d.java" | Out-Null
  & "$bin\comsolbatch.exe" -inputfile "$PWD\$jdir\m_$d.class" -nosave |
    Where-Object { $_ -match "EXPORTED|Error|Failed" }
  & $py drone_20m\comsol_extract.py --design $d
}
Write-Output "==== summary ===="
& $py -c "import pandas as pd; print(pd.read_csv('drone_20m/designs/comsol/comsol_agreement.csv').to_string(index=False))"
