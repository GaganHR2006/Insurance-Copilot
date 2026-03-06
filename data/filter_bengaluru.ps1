# === filter_bengaluru.ps1 ===
# Filters all 4 datasets to only Bengaluru hospitals.
# Overwrites the existing JSON files in-place.

$d = Split-Path -Parent $MyInvocation.MyCommand.Path

# ── Load all datasets ──────────────────────────────────
$hn = Get-Content "$d\hospital_network.json"      | ConvertFrom-Json
$cr = Get-Content "$d\claim_rejection_rates.json"  | ConvertFrom-Json
$te = Get-Content "$d\treatment_exceptions.json"   | ConvertFrom-Json
$ba = Get-Content "$d\bed_availability.json"       | ConvertFrom-Json

# ── Identify Bengaluru hospital IDs ───────────────────
$bengIds = ($hn | Where-Object { $_.city -eq "Bengaluru" }).id
Write-Host "Bengaluru hospitals found: $($bengIds -join ', ')"

# ── 1. hospital_network.json ──────────────────────────
$hn_filtered = $hn | Where-Object { $bengIds -contains $_.id }
$hn_filtered | ConvertTo-Json -Depth 5 | Set-Content "$d\hospital_network.json" -Encoding UTF8
Write-Host "hospital_network.json    -> $($hn_filtered.Count) records"

# ── 2. claim_rejection_rates.json ────────────────────
$cr_filtered = $cr | Where-Object { $bengIds -contains $_.hospital_id }
$cr_filtered | ConvertTo-Json -Depth 5 | Set-Content "$d\claim_rejection_rates.json" -Encoding UTF8
Write-Host "claim_rejection_rates.json -> $($cr_filtered.Count) records"

# ── 3. treatment_exceptions.json ─────────────────────
$te_filtered = $te | Where-Object { $bengIds -contains $_.hospital_id }
$te_filtered | ConvertTo-Json -Depth 5 | Set-Content "$d\treatment_exceptions.json" -Encoding UTF8
Write-Host "treatment_exceptions.json  -> $($te_filtered.Count) records"

# ── 4. bed_availability.json ─────────────────────────
$ba_filtered = $ba | Where-Object { $bengIds -contains $_.hospital_id }
$ba_filtered | ConvertTo-Json -Depth 5 | Set-Content "$d\bed_availability.json" -Encoding UTF8
Write-Host "bed_availability.json      -> $($ba_filtered.Count) records"

Write-Host ""
Write-Host "Done! All datasets now contain only Bengaluru hospitals."
