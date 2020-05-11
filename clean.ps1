#!/usr/bin/env pwsh

$component = Get-Content -Path "component.json" | ConvertFrom-Json
$testImage="$($component.registry)/$($component.name):$($component.version)-test"

# Clean up build directories
if (Test-Path "dist") {
    Remove-Item -Recurse -Force -Path "dist"
}

# Remove docker images
docker rmi $testImage --force
docker image prune --force

# remove cash and temp files 
Remove-Item -Recurse -Force .cache
Remove-Item -Recurse -Force dist
Remove-Item -Recurse -Force pip-services3-mongodb.egg-info
Remove-Item -Force pip-services3-mongodb/*.pyc
Remove-Item -Force pip-services3-mongodb/**/*.pyc
Remove-Item -Recurse -Force test/__pycache__
Remove-Item -Recurse -Force test/**/__pycache__

# Remove existed containers
docker ps -a | Select-String -Pattern "Exit" | foreach($_) { docker rm $_.ToString().Split(" ")[0] }
