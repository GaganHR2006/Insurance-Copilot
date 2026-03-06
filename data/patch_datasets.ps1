# === Patch hospital_network.json and claim_rejection_rates.json ===
# Run from: c:\Users\Pavan Dore\Documents\GitHub\Insurance-Copilot\data\

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ─────────────────────────────────────────────
# PATCH 1: hospital_network.json
# Add fields: type, network_tier
# ─────────────────────────────────────────────

$governmentIds = @("H009", "H010", "H011", "H012", "H013", "H015", "H047")
$trustIds = @("H044")  # Breach Candy Hospital – Trust

$hospitals = Get-Content (Join-Path $scriptDir "hospital_network.json") -Encoding UTF8 | ConvertFrom-Json

$patched = $hospitals | ForEach-Object {
    $h = $_

    # Determine type
    if ($governmentIds -contains $h.id) {
        $type = "Government"
    }
    elseif ($trustIds -contains $h.id) {
        $type = "Trust"
    }
    else {
        $type = "Private"
    }

    # Determine network tier from cashless insurer count
    $count = $h.cashless_insurers.Count
    if ($count -ge 5) {
        $tier = "Tier 1"
    }
    elseif ($count -ge 3) {
        $tier = "Tier 2"
    }
    else {
        $tier = "Tier 3"
    }

    [PSCustomObject]@{
        id                = $h.id
        hospital          = $h.hospital
        city              = $h.city
        type              = $type
        network_tier      = $tier
        cashless_insurers = $h.cashless_insurers
        specialties       = $h.specialties
    }
}

$patched | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $scriptDir "hospital_network.json") -Encoding UTF8
Write-Host "hospital_network.json patched: added 'type' and 'network_tier' to $($patched.Count) records"

# ─────────────────────────────────────────────
# PATCH 2: claim_rejection_rates.json
# Add fields: cashless_supported, common_rejection_reasons
# ─────────────────────────────────────────────

# Build a lookup: hospital_id -> cashless_insurers[]
$cashlessMap = @{}
foreach ($h in $patched) {
    $cashlessMap[$h.id] = $h.cashless_insurers
}

$rejectionReasons = @(
    "Incomplete documents submitted",
    "Pre-existing condition clause invoked",
    "Sub-limit exceeded for this treatment",
    "Treatment not covered under base policy",
    "Waiting period not yet completed",
    "Policy lapsed at time of admission",
    "Non-disclosure of prior medical history",
    "Experimental or investigational treatment",
    "Claim filed after the stipulated deadline",
    "Mismatch between diagnosis and treatment codes",
    "Room rent exceeds policy sub-limit",
    "Procedure categorised as cosmetic exclusion"
)

$rng = [System.Random]::new(77)

$claims = Get-Content (Join-Path $scriptDir "claim_rejection_rates.json") -Encoding UTF8 | ConvertFrom-Json

$claimsPatched = $claims | ForEach-Object {
    $c = $_

    # cashless_supported
    $isCashless = ($cashlessMap[$c.hospital_id] -contains $c.insurer)

    # Number of rejection reasons based on rejection_rate severity
    if ($c.rejection_rate -le 10) {
        $numReasons = 1
    }
    elseif ($c.rejection_rate -le 20) {
        $numReasons = 2
    }
    else {
        $numReasons = 3
    }

    # Pick random unique reasons
    $shuffled = $rejectionReasons | Sort-Object { $rng.Next() }
    $reasons = @($shuffled | Select-Object -First $numReasons)

    [PSCustomObject]@{
        hospital_id              = $c.hospital_id
        hospital                 = $c.hospital
        insurer                  = $c.insurer
        cashless_supported       = $isCashless
        rejection_rate           = $c.rejection_rate
        avg_approval_time_hrs    = $c.avg_approval_time_hrs
        common_rejection_reasons = $reasons
    }
}

$claimsPatched | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $scriptDir "claim_rejection_rates.json") -Encoding UTF8
Write-Host "claim_rejection_rates.json patched: added 'cashless_supported' and 'common_rejection_reasons' to $($claimsPatched.Count) records"

Write-Host "Patch complete!"
