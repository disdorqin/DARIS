$ErrorActionPreference = 'Stop'

$Py = 'C:\ProgramData\anaconda3\envs\daris-research\python.exe'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$InputCsv = 'data/shandong_pmos_hourly.csv'
$PreparedCsv = 'MTGNN/data/shandong_numeric.csv'

New-Item -ItemType Directory -Force -Path 'MTGNN/model' | Out-Null
New-Item -ItemType Directory -Force -Path 'experiment' | Out-Null

# 1) Prepare numeric matrix for MTGNN DataLoaderS.
& $Py 'code/prepare_mtg_data.py' --input $InputCsv --output $PreparedCsv --encoding auto --max_rows 6000

$firstLine = Get-Content $PreparedCsv -TotalCount 1
$numNodes = ($firstLine -split ',').Count

# 2) Baseline run (static graph).
$baselineArgs = @(
  'MTGNN/train_single_step.py',
  '--data', $PreparedCsv,
  '--device', 'cpu',
  '--num_nodes', $numNodes,
  '--epochs', '1',
  '--runs', '1',
  '--batch_size', '32',
  '--seq_in_len', '168',
  '--seq_out_len', '1',
  '--save', 'MTGNN/model/baseline.pt'
)
& $Py @baselineArgs 2>&1 | Tee-Object -FilePath 'experiment/stage3_baseline.log'

# 3) Innovation run (dynamic graph gate).
$dynamicArgs = @(
  'MTGNN/train_single_step.py',
  '--data', $PreparedCsv,
  '--device', 'cpu',
  '--num_nodes', $numNodes,
  '--epochs', '1',
  '--runs', '1',
  '--batch_size', '32',
  '--seq_in_len', '168',
  '--seq_out_len', '1',
  '--dynamic_graph', 'True',
  '--dynamic_graph_alpha', '0.6',
  '--save', 'MTGNN/model/dynamic_graph.pt'
)
& $Py @dynamicArgs 2>&1 | Tee-Object -FilePath 'experiment/stage3_dynamic.log'
