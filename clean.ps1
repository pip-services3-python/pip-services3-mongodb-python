#!/usr/bin/env pwsh

$component = Get-Content -Path "component.json" | ConvertFrom-Json
$docsImage="$($component.registry)/$($component.name):$($component.version)-$($component.build)-docs"
$testImage="$($component.registry)/$($component.name):$($component.version)-$($component.build)-test"

# Clean up build directories
if (Test-Path "dist") {
    Remove-Item -Recurse -Force -Path "dist"
}

# Remove docker images
docker rmi $docsImage --force
docker rmi $testImage --force
docker image prune --force
docker rmi -f $(docker images -f "dangling=true" -q) # remove build container if build fails

# Remove existed containers
$exitedContainers = docker ps -a | Select-String -Pattern "Exit"
foreach($c in $exitedContainers) { docker rm $c.ToString().Split(" ")[0] }

# Remove unused volumes
docker volume rm -f $(docker volume ls -f "dangling=true")

# remove cash and temp files 
Remove-Item -Recurse -Force .cache
Remove-Item -Recurse -Force dist
Remove-Item -Recurse -Force "$($component.name).egg-info"
Remove-Item -Force "$($component.name)/*.pyc"
Remove-Item -Force "$($component.name)/**/*.pyc"
Remove-Item -Recurse -Force test/__pycache__
Remove-Item -Recurse -Force test/**/__pycache__
