# Define parameters
$containerAppName = "containermedchat"
$resourceGroup = "rg-usecase-batch-2024"
$envFilePath = ".env"

# Read and parse the .env file
$envVars = Get-Content $envFilePath |
    Where-Object { $_ -and ($_ -notmatch '^\s*#') } |  # Ignore comments
    ForEach-Object {
        $_.Trim() -replace '"', ''  # Remove surrounding quotes
    }

# Join as comma-separated key=value pairs
$envVarsJoined = $envVars -join ' '

# Run the az containerapp update with --set-env-vars
Write-Host "Updating Azure Container App environment variables..."
Write-Host "Container App Name: $containerAppName"
Write-Host "Resource Group: $resourceGroup"
Write-Host "Environment Variables: $envVarsJoined"
az containerapp update `
  --name $containerAppName `
  --resource-group $resourceGroup `
  --set-env-vars $envVarsJoined
