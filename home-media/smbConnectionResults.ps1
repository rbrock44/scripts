# Define the servers with display names and paths
$servers = @(
    @{ DisplayName = "USBC"; ServerPath = "\\10.0.0.50\usbc"; },
    @{ DisplayName = "USBD"; ServerPath = "\\10.0.0.50\usbd"; },
    @{ DisplayName = "USBE"; ServerPath = "\\10.0.0.50\usbe"; },
    @{ DisplayName = "USBF"; ServerPath = "\\10.0.0.50\usbf"; }
)

# Initialize an array to hold the results
$jsonOutput = @{ results = @() }

# Loop through each server to check the connection status
foreach ($server in $servers) {
    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    
    if (-not [string]::IsNullOrEmpty($server.Username)) {
        # Try to connect to the SMB share with credentials
        $connectionResult = net use * $server.ServerPath /user:$server.Username $server.Password 2>&1
    } else {
        # Try to connect to the SMB share without credentials
        $connectionResult = (net use * $server.ServerPath 2>&1)
    }
	
	$driveLetter = $null
    if ($connectionResult -match '([A-Z]):\\') {
        $driveLetter = $matches[1]
    }

    # Check if the connection was successful
    if ($connectionResult -like "*The command completed successfully.*") {
        $status = "Connected"
    } else {
        $status = "Not Connected"
    }
	
	if ($status -eq "Connected" -and $driveLetter) {
		# Disconnect the mapped drive
		try {
			net use "$($driveLetter):" /delete
		} catch {
			Write-Output "Failed to disconnect drive $driveLetter."
		}
	}

    # Add the result to the output array
    $jsonOutput.results += @{
        DisplayName = $server.DisplayName
        Timestamp = $timestamp
        Status = $status
    }
}

# Define the output file
$outFile = "C:\workspace\drive-status\MediaServerConnectionResults.json"

# Convert the results to JSON and save to a file
$jsonOutput | ConvertTo-Json | Out-File -FilePath $outFile -Encoding utf8

Write-Output "SMB connection status has been recorded in ${outFile}"
