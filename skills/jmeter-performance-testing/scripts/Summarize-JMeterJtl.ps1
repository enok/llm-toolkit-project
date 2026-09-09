param(
    [Parameter(Mandatory = $true)]
    [string]$JtlPath,

    [string]$OutJson = "",
    [string]$OutMarkdown = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-Percentile {
    param(
        [double[]]$Values,
        [double]$Percentile
    )

    if (-not $Values -or $Values.Count -eq 0) {
        return $null
    }

    $sorted = @($Values | Sort-Object)
    if ($sorted.Count -eq 1) {
        return [math]::Round($sorted[0], 2)
    }

    $rank = ($Percentile / 100.0) * ($sorted.Count - 1)
    $lower = [math]::Floor($rank)
    $upper = [math]::Ceiling($rank)
    if ($lower -eq $upper) {
        return [math]::Round($sorted[$lower], 2)
    }

    $weight = $rank - $lower
    $value = ($sorted[$lower] * (1 - $weight)) + ($sorted[$upper] * $weight)
    return [math]::Round($value, 2)
}

$resolvedJtl = Resolve-Path -LiteralPath $JtlPath
$rows = @(Import-Csv -LiteralPath $resolvedJtl.Path)

if ($rows.Count -eq 0) {
    throw "No rows found in JTL: $($resolvedJtl.Path)"
}

$elapsedValues = @(
    foreach ($row in $rows) {
        if ($row.PSObject.Properties.Name -contains "elapsed") {
            [double]$row.elapsed
        }
    }
)

$successRows = @($rows | Where-Object { $_.success -eq "true" -or $_.success -eq "True" })
$failureRows = @($rows | Where-Object { -not ($_.success -eq "true" -or $_.success -eq "True") })
$statusDistribution = @{}
foreach ($group in ($rows | Group-Object responseCode)) {
    $statusDistribution[$group.Name] = $group.Count
}

$labelSummaries = @()
foreach ($labelGroup in ($rows | Group-Object label)) {
    $labelElapsed = @($labelGroup.Group | ForEach-Object { [double]$_.elapsed })
    $labelSuccess = @($labelGroup.Group | Where-Object { $_.success -eq "true" -or $_.success -eq "True" })
    $labelSummaries += [ordered]@{
        label = $labelGroup.Name
        count = $labelGroup.Count
        success = $labelSuccess.Count
        failure = $labelGroup.Count - $labelSuccess.Count
        avgMs = [math]::Round((($labelElapsed | Measure-Object -Average).Average), 2)
        p50Ms = Get-Percentile -Values $labelElapsed -Percentile 50
        p95Ms = Get-Percentile -Values $labelElapsed -Percentile 95
        p99Ms = Get-Percentile -Values $labelElapsed -Percentile 99
        maxMs = [math]::Round((($labelElapsed | Measure-Object -Maximum).Maximum), 2)
    }
}

$summary = [ordered]@{
    jtl = $resolvedJtl.Path
    total = $rows.Count
    success = $successRows.Count
    failure = $failureRows.Count
    successRate = [math]::Round(($successRows.Count / [double]$rows.Count) * 100, 2)
    avgMs = [math]::Round((($elapsedValues | Measure-Object -Average).Average), 2)
    p50Ms = Get-Percentile -Values $elapsedValues -Percentile 50
    p95Ms = Get-Percentile -Values $elapsedValues -Percentile 95
    p99Ms = Get-Percentile -Values $elapsedValues -Percentile 99
    maxMs = [math]::Round((($elapsedValues | Measure-Object -Maximum).Maximum), 2)
    statusDistribution = $statusDistribution
    labels = $labelSummaries
}

$json = $summary | ConvertTo-Json -Depth 6
if ($OutJson) {
    $json | Set-Content -LiteralPath $OutJson -Encoding UTF8
}

if ($OutMarkdown) {
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("# JMeter Summary")
    $lines.Add("")
    $lines.Add(('- Source: `{0}`' -f $resolvedJtl.Path))
    $lines.Add("- Total: $($summary.total)")
    $lines.Add("- Success: $($summary.success)")
    $lines.Add("- Failure: $($summary.failure)")
    $lines.Add("- Success rate: $($summary.successRate)%")
    $lines.Add("- Avg ms: $($summary.avgMs)")
    $lines.Add("- P50 ms: $($summary.p50Ms)")
    $lines.Add("- P95 ms: $($summary.p95Ms)")
    $lines.Add("- P99 ms: $($summary.p99Ms)")
    $lines.Add("- Max ms: $($summary.maxMs)")
    $lines.Add("")
    $lines.Add("## Status Distribution")
    $lines.Add("")
    foreach ($status in ($statusDistribution.Keys | Sort-Object)) {
        $lines.Add(('- `{0}`: {1}' -f $status, $statusDistribution[$status]))
    }
    $lines.Add("")
    $lines.Add("## By Label")
    $lines.Add("")
    $lines.Add("| Label | Count | Success | Failure | Avg ms | P50 ms | P95 ms | P99 ms | Max ms |")
    $lines.Add("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    foreach ($label in $labelSummaries) {
        $lines.Add("| $($label.label) | $($label.count) | $($label.success) | $($label.failure) | $($label.avgMs) | $($label.p50Ms) | $($label.p95Ms) | $($label.p99Ms) | $($label.maxMs) |")
    }
    $lines | Set-Content -LiteralPath $OutMarkdown -Encoding UTF8
}

$json
