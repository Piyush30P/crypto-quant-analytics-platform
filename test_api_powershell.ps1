# Phase 5 API Test Script for PowerShell
# Run this after starting the API server

$separator = "=" * 70
Write-Host $separator
Write-Host "Phase 5: API Testing (PowerShell Edition)"
Write-Host $separator
Write-Host ""

$API_URL = "http://localhost:8000"

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
Write-Host ""
try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/health" -Method Get
    Write-Host "✅ Health Check Passed" -ForegroundColor Green
    Write-Host "  Status: $($response.status)"
    Write-Host "  Version: $($response.version)"
    Write-Host "  Database: $($response.components.database)"
    Write-Host "  Analytics: $($response.components.analytics)"
} catch {
    Write-Host "❌ Health Check Failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
}
Write-Host ""

# Test 2: Statistics Endpoint
Write-Host "Test 2: Statistics Endpoint" -ForegroundColor Yellow
Write-Host ""
try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/stats/BTCUSDT?timeframe=1m&limit=50&rolling_window=10" -Method Get
    Write-Host "✅ Statistics Retrieved" -ForegroundColor Green
    Write-Host "  Symbol: $($response.symbol)"
    Write-Host "  Data Points: $($response.data_points)"
    if ($response.price_stats) {
        Write-Host "  Latest Price: `$$($response.price_stats.latest)"
        Write-Host "  Mean Price: `$$($response.price_stats.mean)"
    }
    if ($response.volatility -and $response.volatility.current) {
        Write-Host "  Volatility: $($response.volatility.current * 100)%"
    } elseif ($response.volatility -and $response.volatility.error) {
        Write-Host "  Volatility: $($response.volatility.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Statistics Failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
}
Write-Host ""

# Test 3: OHLC Data
Write-Host "Test 3: OHLC Data Endpoint" -ForegroundColor Yellow
Write-Host ""
try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/ohlc/BTCUSDT?timeframe=1m&limit=10" -Method Get
    Write-Host "✅ OHLC Data Retrieved" -ForegroundColor Green
    Write-Host "  Symbol: $($response.symbol)"
    Write-Host "  Timeframe: $($response.timeframe)"
    Write-Host "  Bars: $($response.bars.Count)"
    if ($response.bars.Count -gt 0) {
        $latest = $response.bars[-1]
        Write-Host "  Latest Close: `$$($latest.close)"
    }
} catch {
    Write-Host "❌ OHLC Failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
}
Write-Host ""

# Test 4: Pair Analysis
Write-Host "Test 4: Pair Analysis Endpoint" -ForegroundColor Yellow
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
    Write-Host "✅ Pair Analysis Complete" -ForegroundColor Green
    Write-Host "  Pair: $($response.symbol1) vs $($response.symbol2)"
    Write-Host "  Data Points: $($response.data_points)"
    if ($response.correlation) {
        Write-Host "  Correlation: $($response.correlation.pearson)"
        Write-Host "  Strength: $($response.correlation.strength)"
    }
    if ($response.hedge_ratio) {
        Write-Host "  Hedge Ratio: $($response.hedge_ratio.ratio)"
    }
    if ($response.zscore -and $response.zscore.current) {
        Write-Host "  Z-Score: $($response.zscore.current)"
        Write-Host "  Signal: $($response.zscore.signal)"
    }
} catch {
    Write-Host "❌ Pair Analysis Failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
}
Write-Host ""

# Test 5: Available Symbols
Write-Host "Test 5: Available Symbols" -ForegroundColor Yellow
Write-Host ""
try {
    $symbols = Invoke-RestMethod -Uri "$API_URL/api/symbols" -Method Get
    Write-Host "✅ Symbols Retrieved" -ForegroundColor Green
    Write-Host "  Count: $($symbols.Count)"
    if ($symbols.Count -gt 0) {
        Write-Host "  Symbols: $($symbols -join ', ')"
    }
} catch {
    Write-Host "❌ Symbols Failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
}
Write-Host ""

Write-Host $separator
Write-Host "Testing Complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "📚 Interactive Documentation:" -ForegroundColor Cyan
Write-Host "  Swagger UI: http://localhost:8000/docs"
Write-Host "  ReDoc: http://localhost:8000/redoc"
Write-Host $separator
