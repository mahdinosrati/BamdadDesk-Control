#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'
try {
    $profile = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'profile.json') -Raw | ConvertFrom-Json
    $origin = [Uri]$profile.url
    if ($origin.Scheme -ne 'https' -or $origin.UserInfo -or $origin.Query -or $origin.Fragment -or $origin.AbsolutePath -ne '/') { throw 'Invalid HTTPS management origin' }
    if ([Convert]::FromBase64String($profile.public_key).Length -ne 32 -or $profile.token.Length -lt 20) { throw 'Invalid organization profile' }
    $exe = Join-Path $PSScriptRoot 'BamdadDesk.exe'
    if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash -ne $profile.sha256) { throw 'Client checksum mismatch' }
    $management = Join-Path $env:ProgramData 'BamdadDeskManagement'
    if (Test-Path -LiteralPath $management) { throw 'Existing management enrollment found. Use a normal client update; enrollment is not overwritten.' }
    function Protect-Directory([string]$Path, [bool]$Readable) {
        $acl = [Security.AccessControl.DirectorySecurity]::new()
        $acl.SetAccessRuleProtection($true, $false)
        $acl.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
        foreach ($sid in @('S-1-5-18', 'S-1-5-32-544')) {
            $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($sid), 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow'))
        }
        if ($Readable) { $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new('S-1-5-32-545'), 'ReadAndExecute', 'ContainerInherit,ObjectInherit', 'None', 'Allow')) }
        New-Item -ItemType Directory -Path $Path -ErrorAction Stop | Out-Null
        Set-Acl -LiteralPath $Path -AclObject $acl
    }
    Protect-Directory $management $true
    $private = Join-Path $management 'private'
    Protect-Directory $private $false
    Protect-Directory (Join-Path $management 'updates') $true
    $request = @{ url = $profile.url.TrimEnd('/'); public_key = $profile.public_key; token = $profile.token } | ConvertTo-Json
    $requestPath = Join-Path $private 'enrollment.json'
    [IO.File]::WriteAllText($requestPath, $request, [Text.UTF8Encoding]::new($false))
    $fileAcl = Get-Acl -LiteralPath $requestPath
    $fileAcl.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
    Set-Acl -LiteralPath $requestPath -AclObject $fileAcl
    $process = Start-Process -FilePath $exe -ArgumentList '--silent-install' -Wait -PassThru -WindowStyle Hidden
    if ($process.ExitCode -ne 0) { throw "Client installer returned $($process.ExitCode). Enrollment request retained for recovery." }
    Write-Output 'BamdadDesk installed. Registration is automatic when the management service reaches the panel.'
    exit 0
} catch {
    Write-Error $_
    exit 1
}
