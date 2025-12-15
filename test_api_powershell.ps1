# Phase 5 API Test Script for PowerShell

Write-Host "====================================================================="
Write-Host "Phase 5: API Testing (PowerShell Edition)"
Write-Host "====================================================================="
Write-Host ""

$API_URL = "http://localhost:8000"

# Test 1: Health Check
Write-Host "Test 1: Health Check"
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/health" -Method Get
    Write-Host "Health Check Passed"
    Write-Host "Status: $($response.status)"
    Write-Host "Version: $($response.version)"
}
catch {
    Write-Host "Health Check Failed"
    Write-Host $_.Exception.Message
}

Write-Host ""

# Test 2: Statistics
Write-Host "Test 2: Statistics Endpoint"
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/stats/BTCUSDT?timeframe=1m&limit=50&rolling_window=10" -Method Get
    Write-Host "Statistics Retrieved"
    Write-Host "Symbol: $($response.symbol)"
    Write-Host "Data Points: $($response.data_points)"
}
catch {
    Write-Host "Statistics Failed"
    Write-Host $_.Exception.Message
}

Write-Host ""

# Test 3: Pair Analysis
Write-Host "Test 3: Pair Analysis Endpoint"
Write-Host ""

try {
    $body = @{
        symbol1 = "BTCUSDT"
        symbol2 = "ETHUSDT"
        timeframe = "1m"
        rolling_window = 10
        limit = 50
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$API_URL/api/pairs/analyze" -Method Post -Body $body -ContentType "application/json"
    Write-Host "Pair Analysis Complete"
}
catch {
    Write-Host "Pair Analysis Failed"
    Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "====================================================================="
Write-Host "Testing Complete"
Write-Host "====================================================================="
