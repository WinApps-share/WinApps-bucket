param(
    [Parameter(Mandatory = $true)]
    [string]$ActionPath,

    [Parameter(Mandatory = $true)]
    [string]$ReportPath
)

$ErrorActionPreference = 'Stop'
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}
$root = Resolve-Path (Join-Path $PSScriptRoot '..')
$bucket = Join-Path $root 'bucket'
$results = @()
$exitCode = 0

# Excavator only checks manifests that define checkver.
$manifestNames = @(
    Get-ChildItem $bucket -Filter '*.json' -File |
        Where-Object { Select-String -Path $_.FullName -Pattern '"checkver"\s*:' -Quiet } |
        ForEach-Object { $_.BaseName } |
        Sort-Object
)

try {
    Import-Module (Join-Path $ActionPath 'src/Scoop.psm1') -Force
    Import-Module (Join-Path $ActionPath 'src/Helpers.psm1') -Force
    Install-Scoop
    Initialize-NeededConfiguration

    # Scoop's batch error helper prints "$App" ("*") rather than the current
    # manifest, and autoupdate exceptions omit the name. Patch only the runner's
    # temporary Scoop copy so every failure can be attributed and isolated.
    $checkverPath = Join-Path $env:SCOOP_HOME 'bin/checkver.ps1'
    $checkver = Get-Content $checkverPath -Raw
    $checkver = $checkver.Replace(
        'Write-Host "$App`: " -NoNewline',
        'Write-Host "$app`: " -NoNewline'
    )
    $checkver = $checkver.Replace(
        'error $_.Exception.Message',
        'next $_.Exception.Message'
    )
    Set-Content -Path $checkverPath -Value $checkver -Encoding utf8

    $logPath = Join-Path $env:RUNNER_TEMP 'excavator.log'
    $arguments = @(
        '-NoProfile', '-File', $checkverPath,
        '-App', '*',
        '-Dir', $bucket,
        '-Update',
        '-SkipUpdated'
    )

    # checkver handles manifest-level errors internally and continues checking.
    # Run it without ThrowError so one bad manifest cannot abort the batch.
    & pwsh @arguments 2>&1 | Tee-Object -FilePath $logPath
    $checkExitCode = $LASTEXITCODE

    $failedNames = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::OrdinalIgnoreCase
    )
    Get-Content $logPath | ForEach-Object {
        $line = $_ -replace '\x1b\[[0-9;]*m', ''
        if ($line -match '^(?<name>[^:\s]+):\s*(?<message>.+)$') {
            $name = $Matches.name
            $message = $Matches.message
            $isVersionResult = $message -match '^\S+ \(scoop version is .+\)( autoupdate available)?$'
            if ($manifestNames -contains $name -and -not $isVersionResult) {
                [void]$failedNames.Add($name)
            }
        }
    }

    # Discard only the failed manifest's partial update. Other manifests remain
    # available for independent commits.
    foreach ($name in $failedNames) {
        git -C $root restore --staged --worktree -- "bucket/$name.json"
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to restore bucket/$name.json"
        }
    }

    $changedNames = @(
        git -C $root diff --name-only -- bucket |
            Where-Object { $_ -match '^bucket/(.+)\.json$' } |
            ForEach-Object { [System.IO.Path]::GetFileNameWithoutExtension($_) } |
            Where-Object { $manifestNames -contains $_ } |
            Sort-Object -Unique
    )
    $updatedNames = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::OrdinalIgnoreCase
    )

    # Commit each manifest separately. A commit failure rolls back only that
    # manifest and does not block the remaining successful updates.
    foreach ($name in $changedNames) {
        try {
            $manifestPath = "bucket/$name.json"
            $versionLine = Select-String -Path (Join-Path $root $manifestPath) `
                -Pattern '"version"\s*:\s*"(?<version>[^"]+)"' |
                Select-Object -First 1
            $version = if ($versionLine) { $versionLine.Matches[0].Groups['version'].Value } else { 'unknown' }

            git -C $root add -- $manifestPath
            if ($LASTEXITCODE -ne 0) { throw "git add failed for $name" }
            git -C $root commit -m "$name`: Update to version $version" -- $manifestPath
            if ($LASTEXITCODE -ne 0) { throw "git commit failed for $name" }
            [void]$updatedNames.Add($name)
        }
        catch {
            Write-Host "::error title=$name 提交失败::$($_.Exception.Message)"
            [void]$failedNames.Add($name)
            git -C $root restore --staged --worktree -- "bucket/$name.json"
        }
    }

    foreach ($name in $manifestNames) {
        $results += [ordered]@{
            name = $name
            status = if ($failedNames.Contains($name)) { 'failed' } else { 'success' }
            updated = $updatedNames.Contains($name)
        }
    }

    if ($checkExitCode -ne 0) {
        $results += [ordered]@{
            name = 'excavator'
            status = 'failed'
            updated = $false
            error = "checkver exited with code $checkExitCode"
        }
    }

    # Push all successful commits once, after every manifest has been processed.
    # A check failure therefore cannot prevent unrelated commits from being made.
    if ($updatedNames.Count -gt 0) {
        git -C $root push
        if ($LASTEXITCODE -ne 0) {
            throw 'git push failed'
        }
    }
    if ($failedNames.Count -gt 0 -or $checkExitCode -ne 0) {
        $exitCode = 1
    }
}
catch {
    Write-Host "::error title=Excavator 执行失败::$($_.Exception.Message)"
    $results += [ordered]@{
        name = 'excavator'
        status = 'failed'
        updated = $false
        error = $_.Exception.Message
    }
    $exitCode = 1
}
finally {
    $succeeded = @($results | Where-Object { $_.status -eq 'success' }).Count
    $updated = @($results | Where-Object { $_.status -eq 'success' -and $_.updated }).Count
    $failed = @($results | Where-Object { $_.status -eq 'failed' }).Count
    $report = [ordered]@{
        checked = $manifestNames.Count
        succeeded = $succeeded
        updated = $updated
        unchanged = $succeeded - $updated
        failed = $failed
        results = $results
    }
    $reportDirectory = Split-Path $ReportPath -Parent
    New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null
    $report | ConvertTo-Json -Depth 5 | Set-Content -Path $ReportPath -Encoding utf8
}

exit $exitCode
