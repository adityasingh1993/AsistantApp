Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AppAI Hub — Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Ollama
$ollamaRunning = $false
try {
    $r = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    $ollamaRunning = $true
    Write-Host "[OK] Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Ollama not detected at localhost:11434" -ForegroundColor Yellow
    Write-Host "       LLM calls will fail until Ollama is started." -ForegroundColor Yellow
    Write-Host "       Install from: https://ollama.ai" -ForegroundColor Yellow
    Write-Host "       Then run: ollama pull qwen2.5:7b" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "[..] Starting AppAI Hub on ws://localhost:7788 ..." -ForegroundColor Cyan
Write-Host "     Admin API: http://localhost:7788/health" -ForegroundColor Gray
Write-Host "     API Docs:  http://localhost:7788/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

Set-Location "$PSScriptRoot\appai-hub"
python -m uvicorn main:app --host 0.0.0.0 --port 7788 --reload
