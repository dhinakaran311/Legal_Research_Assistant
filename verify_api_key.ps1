# PowerShell script to verify INTERNAL_API_KEY configuration
# Checks if AI Engine and Backend have matching API keys

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🔐 INTERNAL_API_KEY Verification" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = $PSScriptRoot
$aiEngineEnv = Join-Path $projectRoot "ai_engine\.env"
$backendEnv = Join-Path $projectRoot "backend\.env"

# Check AI Engine .env
Write-Host "Checking AI Engine .env..." -ForegroundColor Yellow
if (Test-Path $aiEngineEnv) {
    Write-Host "✅ AI Engine .env found: $aiEngineEnv" -ForegroundColor Green
    
    $aiEngineContent = Get-Content $aiEngineEnv -Raw
    if ($aiEngineContent -match 'INTERNAL_API_KEY\s*=\s*(.+)') {
        $aiEngineKey = $matches[1].Trim()
        if ($aiEngineKey -match '^["''](.+)["'']$') {
            $aiEngineKey = $matches[1]
        }
        $keyPreview = if ($aiEngineKey.Length -gt 30) { 
            $aiEngineKey.Substring(0, 20) + "..." + $aiEngineKey.Substring($aiEngineKey.Length - 10)
        } else { 
            $aiEngineKey 
        }
        Write-Host "   INTERNAL_API_KEY: $keyPreview" -ForegroundColor White
    } else {
        Write-Host "   ⚠️  INTERNAL_API_KEY not found in .env file" -ForegroundColor Yellow
        $aiEngineKey = $null
    }
} else {
    Write-Host "❌ AI Engine .env not found: $aiEngineEnv" -ForegroundColor Red
    Write-Host "   Create this file with INTERNAL_API_KEY" -ForegroundColor Yellow
    $aiEngineKey = $null
}

Write-Host ""

# Check Backend .env
Write-Host "Checking Backend .env..." -ForegroundColor Yellow
if (Test-Path $backendEnv) {
    Write-Host "✅ Backend .env found: $backendEnv" -ForegroundColor Green
    
    $backendContent = Get-Content $backendEnv -Raw
    if ($backendContent -match 'INTERNAL_API_KEY\s*=\s*(.+)') {
        $backendKey = $matches[1].Trim()
        if ($backendKey -match '^["''](.+)["'']$') {
            $backendKey = $matches[1]
        }
        $keyPreview = if ($backendKey.Length -gt 30) { 
            $backendKey.Substring(0, 20) + "..." + $backendKey.Substring($backendKey.Length - 10)
        } else { 
            $backendKey 
        }
        Write-Host "   INTERNAL_API_KEY: $keyPreview" -ForegroundColor White
    } else {
        Write-Host "   ⚠️  INTERNAL_API_KEY not found in .env file" -ForegroundColor Yellow
        $backendKey = $null
    }
} else {
    Write-Host "❌ Backend .env not found: $backendEnv" -ForegroundColor Red
    Write-Host "   Create this file with INTERNAL_API_KEY" -ForegroundColor Yellow
    $backendKey = $null
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

# Verification
if (-not $aiEngineKey -or -not $backendKey) {
    Write-Host "⚠️  VERIFICATION FAILED" -ForegroundColor Red
    Write-Host ""
    if (-not $aiEngineKey) {
        Write-Host "   ❌ AI Engine INTERNAL_API_KEY is missing" -ForegroundColor Red
    }
    if (-not $backendKey) {
        Write-Host "   ❌ Backend INTERNAL_API_KEY is missing" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "💡 Solution:" -ForegroundColor Yellow
    Write-Host "   1. Create .env files in both ai_engine/ and backend/" -ForegroundColor White
    Write-Host "   2. Set INTERNAL_API_KEY in both files" -ForegroundColor White
    Write-Host "   3. Make sure they match exactly" -ForegroundColor White
    exit 1
}

if ($aiEngineKey -eq $backendKey) {
    Write-Host "✅ VERIFICATION PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "   Both AI Engine and Backend have matching API keys" -ForegroundColor White
    Write-Host "   Key length: $($aiEngineKey.Length) characters" -ForegroundColor White
    Write-Host ""
    Write-Host "   🎉 Configuration is correct!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ VERIFICATION FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "   API keys do NOT match!" -ForegroundColor Red
    Write-Host ""
    $aiPreview = if ($aiEngineKey.Length -gt 40) { 
        $aiEngineKey.Substring(0, 30) + "..." 
    } else { 
        $aiEngineKey 
    }
    $backendPreview = if ($backendKey.Length -gt 40) { 
        $backendKey.Substring(0, 30) + "..." 
    } else { 
        $backendKey 
    }
    Write-Host "   AI Engine key:  $aiPreview" -ForegroundColor White
    Write-Host "   Backend key:    $backendPreview" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 Solution:" -ForegroundColor Yellow
    Write-Host "   1. Copy the same INTERNAL_API_KEY to both .env files" -ForegroundColor White
    Write-Host "   2. Make sure there are no extra spaces or quotes" -ForegroundColor White
    Write-Host "   3. Restart both services after updating" -ForegroundColor White
    exit 1
}
