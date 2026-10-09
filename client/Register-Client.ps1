#Requires -RunAsAdministrator
param([string]$PanelUrl, [string]$PublicKey)
$ErrorActionPreference = 'Stop'
if (-not $PanelUrl) { $PanelUrl = Read-Host 'Panel HTTPS origin (example https://desk.example.com)' }
if (-not $PublicKey) { $PublicKey = Read-Host 'Policy public key shown by the panel' }
$uri = [Uri]$PanelUrl
if (-not $uri.IsAbsoluteUri -or $uri.Scheme -ne 'https' -or $uri.UserInfo -or $uri.Query -or $uri.Fragment -or $uri.AbsolutePath -ne '/') {
    throw 'Use an HTTPS origin without path, credentials, query or fragment.'
}
if ([Convert]::FromBase64String($PublicKey).Length -ne 32) { throw 'Invalid Ed25519 public key.' }
$managementPath = [IO.Path]::GetFullPath((Join-Path $env:ProgramData 'BamdadDeskManagement'))
$privatePath = Join-Path $managementPath 'private'
if (Test-Path $managementPath) { throw 'Management directory already exists. Follow the documented administrator re-enrollment procedure; existing state will not be overwritten.' }
if (Test-Path (Join-Path $privatePath 'credentials.json')) { throw 'Device already enrolled. Re-enrollment requires the documented administrator removal procedure.' }
if (Test-Path (Join-Path $privatePath 'enrollment.json')) { throw 'An enrollment request already exists. Check the installed managed client before replacing it.' }
$secretToken = Read-Host 'Enrollment token (hidden)' -AsSecureString
$tokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretToken)
try {
    $plainToken = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPointer)
    if ($plainToken.Length -lt 20 -or $plainToken.Length -gt 200) { throw 'Invalid enrollment token.' }
    function Set-ManagementAcl([string]$Path, [bool]$ReadableByUsers) {
        $acl = [Security.AccessControl.DirectorySecurity]::new()
        $acl.SetAccessRuleProtection($true, $false)
        $acl.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
        foreach ($sid in @('S-1-5-18', 'S-1-5-32-544')) {
            $rule = [Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($sid), 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
            $acl.AddAccessRule($rule)
        }
        if ($ReadableByUsers) {
            $rule = [Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new('S-1-5-32-545'), 'ReadAndExecute', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
            $acl.AddAccessRule($rule)
        }
        Set-Acl -LiteralPath $Path -AclObject $acl
    }
    New-Item -ItemType Directory -Force -Path $managementPath | Out-Null
    Set-ManagementAcl $managementPath $true
    New-Item -ItemType Directory -Force -Path $privatePath | Out-Null
    Set-ManagementAcl $privatePath $false
    New-Item -ItemType Directory -Force -Path (Join-Path $managementPath 'updates') | Out-Null
    Set-ManagementAcl (Join-Path $managementPath 'updates') $true
    $request = @{ url = $PanelUrl.TrimEnd('/'); public_key = $PublicKey; token = $plainToken } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $privatePath 'enrollment.json'), $request, [Text.UTF8Encoding]::new($false))
    $fileAcl = Get-Acl -LiteralPath (Join-Path $privatePath 'enrollment.json')
    $fileAcl.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
    Set-Acl -LiteralPath (Join-Path $privatePath 'enrollment.json') -AclObject $fileAcl
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer)
    $plainToken = $null
    $request = $null
    $secretToken.Dispose()
}
Write-Host 'Enrollment staged. The installed BamdadDesk managed service checks it within 60 seconds.'
Write-Host 'The existing service was not restarted. Install the managed client build if it is not installed yet.'
