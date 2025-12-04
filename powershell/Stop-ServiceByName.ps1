param(
    [Parameter(Mandatory = $true)]
    [string]$ServiceName
)

# Try to get the service
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if (-not $service) {
    Write-Output "Service '$ServiceName' was not found."
    exit 1
}

Write-Output "Service '$ServiceName' found. Current status: $($service.Status)"

# Stop if it's already stopped
if ($service.Status -eq 'Stopped') {
    Write-Output "Service '$ServiceName' is already stopped."
    exit 0
}

try {
    Write-Output "Attempting to stop service '$ServiceName'..."
    Stop-Service -Name $ServiceName -Force -ErrorAction Stop

    # Wait for it to fully stop
    $service.WaitForStatus('Stopped', '00:00:10')

    Write-Output "Service '$ServiceName' has been successfully stopped."
}
catch {
    Write-Output "Failed to stop service '$ServiceName'. Error: $($_.Exception.Message)"
    exit 1
}
