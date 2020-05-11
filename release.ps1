#!/usr/bin/env pwsh

Set-StrictMode -Version latest
$ErrorActionPreference = "Stop"

$component = Get-Content -Path "component.json" | ConvertFrom-Json

if ([string]::IsNullOrEmpty($component.version)) {
    throw "Versions in component.json do not set"
}


# Publish to global repository
Write-Output "Pushing package to pipy"
python setup.py sdist
twine upload --skip-existing dist/*