# === Generate treatment_exceptions.json and bed_availability.json ===
# Run from: c:\Users\Pavan Dore\Documents\GitHub\Insurance-Copilot\data\

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$hospitalFile = Join-Path $scriptDir "hospital_network.json"
$hospitals = Get-Content $hospitalFile | ConvertFrom-Json

$treatments = @(
    "Angioplasty", "Knee Replacement", "Chemotherapy", "Dialysis",
    "LASIK Surgery", "Cataract Surgery", "Appendectomy",
    "Cesarean Section", "Spinal Fusion", "Liver Transplant"
)

$insurers = @("StarHealth", "NivaBupa", "HDFCErgo", "ICICILombard", "BajajAllianz")

$notCoveredNotes = @(
    "Requires pre-authorization",
    "Not covered under base policy",
    "Covered only with top-up plan",
    "Waiting period of 2 years applies",
    "Sub-limit of Rs.50,000 applies"
)

# ===== DATASET 3: treatment_exceptions.json (2500 records — all 50 hospitals) =====
$records = @()
$rng = [System.Random]::new(42)

foreach ($treatment in $treatments) {
    foreach ($hospital in $hospitals) {
        # <-- was: Select-Object -First 20
        foreach ($insurer in $insurers) {
            $covered = ($rng.NextDouble() -lt 0.75)
            $note = if ($covered) {
                "Covered under standard policy"
            }
            else {
                $notCoveredNotes[$rng.Next(0, $notCoveredNotes.Length)]
            }
            $records += [PSCustomObject]@{
                treatment   = $treatment
                hospital_id = $hospital.id
                hospital    = $hospital.hospital
                insurer     = $insurer
                policy      = "$insurer Health Shield"
                covered     = $covered
                note        = $note
            }
        }
    }
}

$records | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $scriptDir "treatment_exceptions.json") -Encoding UTF8
Write-Host "treatment_exceptions.json written: $($records.Count) records"

# ===== DATASET 4: bed_availability.json (50 records) =====
$bedRecords = @()
$rng2 = [System.Random]::new(99)
$baseTime = [System.DateTimeOffset]::Parse("2026-03-06T08:00:00Z")

foreach ($hospital in $hospitals) {
    $icuTotal = $rng2.Next(10, 81)
    $icuAvail = $rng2.Next(0, [Math]::Min(31, $icuTotal + 1))
    $genTotal = $rng2.Next(50, 501)
    $genAvail = $rng2.Next(5, [Math]::Min(201, $genTotal + 1))

    # Specialty beds capped to fraction of ICU total
    $cardiacIcu = $rng2.Next(1, [Math]::Max(2, [int]([Math]::Ceiling($icuTotal * 0.35))))
    $neonatalIcu = $rng2.Next(0, [Math]::Max(2, [int]([Math]::Ceiling($icuTotal * 0.25))))
    $oncologyBeds = $rng2.Next(2, [Math]::Max(3, [int]([Math]::Ceiling($genTotal * 0.10))))

    # Varied last_updated: random offset 0–119 minutes from base
    $offsetMins = $rng2.Next(0, 120)
    $updatedAt = $baseTime.AddMinutes(-$offsetMins).ToString("yyyy-MM-ddTHH:mm:ssZ")

    $bedRecords += [PSCustomObject]@{
        hospital_id    = $hospital.id
        hospital       = $hospital.hospital
        city           = $hospital.city
        icu_beds       = [PSCustomObject]@{ total = $icuTotal; available = $icuAvail }
        general_beds   = [PSCustomObject]@{ total = $genTotal; available = $genAvail }
        specialty_beds = [PSCustomObject]@{
            cardiac_icu  = $cardiacIcu
            neonatal_icu = $neonatalIcu
            oncology     = $oncologyBeds
        }
        waitlist_count = $rng2.Next(0, 31)
        last_updated   = $updatedAt
    }
}

$bedRecords | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $scriptDir "bed_availability.json") -Encoding UTF8
Write-Host "bed_availability.json written: $($bedRecords.Count) records"

Write-Host "All done!"
