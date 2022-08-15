#!/usr/bin/env pwsh

# Get component metadata and set necessary variables
$component = Get-Content -Path "$PSScriptRoot/component.json" | ConvertFrom-Json
$testImage = "$($component.registry)/$($component.name):$($component.version)-$($component.build)-test"
$rcImage = "$($component.registry)/$($component.name):$($component.version)-$($component.build)"
$latestImage = "$($component.registry)/$($component.name):latest"

# Remove docker images
docker rmi $testImage --force
docker rmi $rcImage --force
docker rmi $latestImage --force
docker rmi -f $(docker images -f "dangling=true" -q) # remove build container if build fails
docker image prune --force

# Remove existed containers
$exitedContainers = docker ps -a | Select-String -Pattern "Exit"
foreach($c in $exitedContainers) { docker rm $c.ToString().Split(" ")[0] }

# Remove unused volumes
docker volume rm -f $(docker volume ls -f "dangling=true")

# Remove cash and temp files 
if (Test-Path -Path "$PSScriptRoot/cache") {
    Remove-Item -Path "$PSScriptRoot/cache" -Recurse -Force
}
if (Test-Path -Path "$PSScriptRoot/dist") {
    Remove-Item -Path "$PSScriptRoot/dist" -Recurse -Force
}
if (Test-Path -Path "$PSScriptRoot/$($component.name.replace('-', '_')).egg-info") {
    Remove-Item -Path "$PSScriptRoot/$($component.name.replace('-', '_')).egg-info" -Recurse -Force
}
if (Test-Path -Path "$PSScriptRoot/$($component.name.replace('-', '_')).egg-info") {
    Remove-Item -Path "$PSScriptRoot/$($component.name.replace('-', '_')).egg-info" -Recurse -Force
}
if (Test-Path -Path "$PSScriptRoot/$($component.name.replace('-', '_'))/*.pyc") {
    Remove-Item -Path "$PSScriptRoot/$($component.name.replace('-', '_'))/*.pyc" -Recurse -Force
}
if (Test-Path -Path "$PSScriptRoot/$($component.name.replace('-', '_'))/**/*.pyc") {
    Remove-Item -Path "$PSScriptRoot/$($component.name.replace('-', '_'))/**/*.pyc" -Recurse -Force
}
if (Test-Path -Path "$PSScriptRoot/$($component.name.replace('-', '_'))/__pycache__") {
    Remove-Item -Path "$PSScriptRoot/$($component.name.replace('-', '_'))/__pycache__" -Recurse -Force
}
if (Test-Path -Path "$PSScriptRoot/test/__pycache__") {
    Remove-Item -Path "$PSScriptRoot/test/__pycache__" -Recurse -Force
}
if (Test-Path -Path "$PSScriptRoot/test/**/__pycache__") {
    Remove-Item -Path "$PSScriptRoot/test/**/__pycache__" -Recurse -Force
}
if (Test-Path -Path "$PSScriptRoot/test/.pytest_cache") {
    Remove-Item -Path "$PSScriptRoot/test/.pytest_cache" -Recurse -Force
}
if (Test-Path -Path "$PSScriptRoot/test/**/.pytest_cache") {
    Remove-Item -Path "$PSScriptRoot/test/**/.pytest_cache" -Recurse -Force
}
