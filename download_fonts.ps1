$ErrorActionPreference = "Stop"

$scriptDir = $PSScriptRoot
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }

$interDir = Join-Path $scriptDir "static/fonts/inter"
$phosphorDir = Join-Path $scriptDir "static/fonts/phosphor"

# Create directories
New-Item -ItemType Directory -Path $interDir -Force | Out-Null
New-Item -ItemType Directory -Path $phosphorDir -Force | Out-Null

# 1. Download Inter CSS & Font Files
$ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
$interUrl = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
Write-Host "Fetching Inter CSS from $interUrl..."
$interCss = (Invoke-WebRequest -Uri $interUrl -Headers @{'User-Agent'=$ua} -UseBasicParsing).Content

# Find all font URLs in inter CSS
$regex = [regex]'url\((https://fonts\.gstatic\.com/[^)]+)\)'
$matches = $regex.Matches($interCss)

$downloaded = @{}
foreach ($m in $matches) {
    $url = $m.Groups[1].Value
    $filename = Split-Path $url -Leaf
    if (-not $downloaded.ContainsKey($filename)) {
        Write-Host "Downloading $filename..."
        Invoke-WebRequest -Uri $url -OutFile (Join-Path $interDir $filename) -UseBasicParsing
        $downloaded[$filename] = $true
    }
    $interCss = $interCss.Replace($url, $filename)
}

# Also ensure variable font inter-latin.woff2 exists if requested specifically
$varFontUrl = 'https://fonts.gstatic.com/s/inter/v18/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfAZ9hiJ-Ek-_EeA.woff2'
try {
    Write-Host "Downloading inter-latin.woff2..."
    Invoke-WebRequest -Uri $varFontUrl -OutFile (Join-Path $interDir 'inter-latin.woff2') -UseBasicParsing
} catch {
    Write-Warning "Could not download inter-latin.woff2: $_"
}

Set-Content -Path (Join-Path $interDir "inter.css") -Value $interCss -Encoding UTF8
Write-Host "Saved $(Join-Path $interDir 'inter.css')"

# 2. Download Phosphor Icons (bold, fill, duotone)
$weights = @('bold', 'fill', 'duotone')
foreach ($w in $weights) {
    $cssUrl = "https://unpkg.com/@phosphor-icons/web@2.1.1/src/$w/style.css"
    Write-Host "Fetching $w CSS from $cssUrl..."
    $cssContent = (Invoke-WebRequest -Uri $cssUrl -UseBasicParsing).Content

    # Find font URLs in CSS
    $fontRegex = [regex]"url\((?:`"|')?([^`"')]+)"
    $fontMatches = $fontRegex.Matches($cssContent)
    
    foreach ($fm in $fontMatches) {
        $relPath = $fm.Groups[1].Value
        if ($relPath -like "data:*") { continue }
        
        $fontName = (Split-Path $relPath -Leaf) -replace '#.*$', ''
        $fontUrl = "https://unpkg.com/@phosphor-icons/web@2.1.1/src/$w/$fontName"
        
        Write-Host "Downloading $fontName from $fontUrl..."
        try {
            Invoke-WebRequest -Uri $fontUrl -OutFile (Join-Path $phosphorDir $fontName) -UseBasicParsing
            $cssContent = $cssContent.Replace($relPath, $fontName)
        } catch {
            Write-Warning "Could not download ${fontUrl}: $_"
        }
    }
    
    Set-Content -Path (Join-Path $phosphorDir "$w.css") -Value $cssContent -Encoding UTF8
    Write-Host "Saved $(Join-Path $phosphorDir "$w.css")"
}

Write-Host "All assets downloaded successfully!"
