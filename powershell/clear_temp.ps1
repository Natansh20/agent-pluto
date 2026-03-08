Write-Output "Clearing user temp files..."
Remove-Item -Path $env:TEMP\* -Recurse -Force -ErrorAction SilentlyContinue