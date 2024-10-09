# Define servers in a list
$servers = @(
    @{ DisplayName = "USBC"; ServerPath = "\\10.0.0.50\usbc"; Username = ""; Password = "" },
    @{ DisplayName = "USBD"; ServerPath = "\\10.0.0.50\usbd"; Username = ""; Password = "" },
    @{ DisplayName = "USBE"; ServerPath = "\\10.0.0.50\usbe"; Username = ""; Password = "" },
	@{ DisplayName = "USBF"; ServerPath = "\\10.0.0.50\usbf"; Username = ""; Password = "" }
)

# Initialize an array to hold the results
$results = @()

foreach ($server in $servers) {
    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    
    if (-not [string]::IsNullOrEmpty($server.Username)) {
        # Try to connect to the SMB share with credentials
        $connectionResult = net use * $server.ServerPath /user:$server.Username $server.Password 2>&1
    } else {
        # Try to connect to the SMB share without credentials
        $connectionResult = net use * $server.ServerPath 2>&1
    }

    if ($connectionResult -like "*The command completed successfully.*") {
        $status = "Connected"
    } else {
        $status = "Not Connected"
    }

    $results += @{
        DisplayName = $server.DisplayName
        Timestamp = $timestamp
        Status = $status
    }
	
	net use * /delete /y > $null
}

$jsonOutput = @{
    results = $results
}


# edit this more, to save and push
$outFile = "MediaServerConnectionResults.json"

$jsonOutput | ConvertTo-Json| Out-File $outFile

Write-Output "SMB connection status has been recorded in ${outFile}"
