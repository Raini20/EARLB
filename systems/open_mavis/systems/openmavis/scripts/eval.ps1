# Auswertung eines Laufs mit dem gemeinsamen Image earlb-eval (Windows, PowerShell).
# Aufruf (egal aus welchem Ordner):  .\systems\openmavis\scripts\eval.ps1 1
# Erzeugt in results/exp14/run_<n>/: ape.zip, rpe_trans.zip, rpe_rot.zip, ape.txt, rpe_*.txt, traj_xy.pdf
param([Parameter(Mandatory=$true)][int]$Run)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..\..\..").Path
docker image inspect earlb-eval *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Baue earlb-eval (einmalig) ..."
    docker build -t earlb-eval -f "$Root\common\eval\Dockerfile" "$Root\common\eval"
}
$commit = git -C $Root rev-parse --short HEAD
docker run --rm -e GIT_COMMIT=$commit -v "${Root}:/repo" earlb-eval bash common/eval/evaluate.sh openmavis $Run
