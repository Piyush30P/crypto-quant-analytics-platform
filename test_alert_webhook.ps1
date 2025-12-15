# PowerShell script to test alert system with webhook
# Run this script: .\test_alert_webhook.ps1

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "Testing Alert System with Webhook" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

$API_BASE_URL = "http://localhost:8000"

# Step 1: Instructions for webhook
Write-Host "Step 1: Get a Webhook URL" -ForegroundColor Yellow
Write-Host "  1. Open https://webhook.site in your browser" -ForegroundColor White
Write-Host "  2. Copy your unique webhook URL" -ForegroundColor White
Write-Host "  3. Paste it below when prompted" -ForegroundColor White
Write-Host ""

$webhookUrl = Read-Host "Enter your webhook.site URL (or press Enter to skip)"

if ([string]::IsNullOrWhiteSpace($webhookUrl)) {
    $webhookUrl = "https://webhook.site/test-placeholder"
    Write-Host "  Using placeholder URL (notifications won't be sent)" -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Create alert rule
Write-Host "Step 2: Creating Alert Rule" -ForegroundColor Yellow

$alertRule = @{
    name = "BTC-ETH Z-Score Alert (Sensitive)"
    alert_type = "zscore_threshold"
    symbol1 = "BTCUSDT"
    symbol2 = "ETHUSDT"
    timeframe = "1m"
    threshold_upper = 1.5
    threshold_lower = -1.5
    notification_channels = @("webhook")
    notification_config = @{
        webhook = @{
            url = $webhookUrl
        }
    }
    cooldown_minutes = 5
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$API_BASE_URL/api/alerts/rules" `
        -Method Post `
        -ContentType "application/json" `
        -Body $alertRule

    Write-Host "  [OK] Alert rule created successfully!" -ForegroundColor Green
    Write-Host "    - ID: $($response.id)" -ForegroundColor White
    Write-Host "    - Name: $($response.name)" -ForegroundColor White
    Write-Host "    - Type: $($response.alert_type)" -ForegroundColor White
    Write-Host "    - Pair: $($response.symbol1) vs $($response.symbol2)" -ForegroundColor White
    Write-Host "    - Thresholds: $($response.threshold_lower) < Z-score < $($response.threshold_upper)" -ForegroundColor White
    Write-Host "    - Status: $($response.status)" -ForegroundColor White

    $ruleId = $response.id
} catch {
    Write-Host "  [ERROR] Failed to create alert rule: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Trigger manual check
Write-Host "Step 3: Triggering Manual Alert Check" -ForegroundColor Yellow

try {
    $checkResponse = Invoke-RestMethod -Uri "$API_BASE_URL/api/alerts/monitor/check" `
        -Method Post `
        -ContentType "application/json"

    Write-Host "  [OK] Manual check completed!" -ForegroundColor Green
    Write-Host "    - Total rules: $($checkResponse.total_rules)" -ForegroundColor White
    Write-Host "    - Triggered: $($checkResponse.triggered)" -ForegroundColor White
    Write-Host "    - Skipped: $($checkResponse.skipped)" -ForegroundColor White
    Write-Host "    - Errors: $($checkResponse.errors)" -ForegroundColor White
    Write-Host "    - Timestamp: $($checkResponse.timestamp)" -ForegroundColor White

    if ($checkResponse.triggered -gt 0) {
        Write-Host ""
        Write-Host "  [ALERT!] $($checkResponse.triggered) alert(s) were triggered!" -ForegroundColor Green
        Write-Host "  Check your webhook.site URL to see the notification!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "  [INFO] No alerts triggered yet (Z-score hasn't crossed +/-1.5)" -ForegroundColor Cyan
        Write-Host "  The background monitor will check every 60 seconds" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  [ERROR] Failed to trigger manual check: $_" -ForegroundColor Red
}

Write-Host ""

# Step 4: View all active rules
Write-Host "Step 4: Viewing All Active Rules" -ForegroundColor Yellow

try {
    $rules = Invoke-RestMethod -Uri "$API_BASE_URL/api/alerts/rules" -Method Get

    Write-Host "  [OK] Retrieved $($rules.Count) alert rule(s)" -ForegroundColor Green
    foreach ($rule in $rules) {
        Write-Host "    - $($rule.name) (ID: $($rule.id), Status: $($rule.status))" -ForegroundColor White
    }
} catch {
    Write-Host "  [ERROR] Failed to get rules: $_" -ForegroundColor Red
}

Write-Host ""

# Step 5: View alert history
Write-Host "Step 5: Viewing Alert History" -ForegroundColor Yellow

try {
    $history = Invoke-RestMethod -Uri "$API_BASE_URL/api/alerts/history?limit=10" -Method Get

    Write-Host "  [OK] Retrieved $($history.Count) alert history item(s)" -ForegroundColor Green

    if ($history.Count -gt 0) {
        Write-Host ""
        Write-Host "  Recent alerts:" -ForegroundColor Cyan
        foreach ($item in $history | Select-Object -First 5) {
            Write-Host "    - [$($item.alert_type)] $($item.symbol1) vs $($item.symbol2)" -ForegroundColor White
            Write-Host "      Triggered: $($item.triggered_at)" -ForegroundColor Gray
            Write-Host "      Z-Score: $([math]::Round($item.trigger_value, 4)) (threshold: $([math]::Round($item.threshold_breached, 2)))" -ForegroundColor Gray
            if ($item.notifications_sent -and $item.notifications_sent.Count -gt 0) {
                Write-Host "      Notifications: $($item.notifications_sent -join ', ')" -ForegroundColor Green
            }
            if ($item.notification_errors -and $item.notification_errors.Count -gt 0) {
                Write-Host "      Errors: $($item.notification_errors -join ', ')" -ForegroundColor Red
            }
            Write-Host ""
        }
    } else {
        Write-Host "    No alerts triggered yet - monitor is checking every 60s" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  [ERROR] Failed to get alert history: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "[SUCCESS] Alert System Test Complete!" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""
Write-Host "[TIP] What's happening now:" -ForegroundColor Yellow
Write-Host "  - Background monitor checks all rules every 60 seconds" -ForegroundColor White
Write-Host "  - When BTCUSDT/ETHUSDT Z-score crosses +/-1.5, alert triggers" -ForegroundColor White
Write-Host "  - Notification will be sent to your webhook URL" -ForegroundColor White
Write-Host "  - 5-minute cooldown prevents spam" -ForegroundColor White
Write-Host ""
Write-Host "[DASHBOARD] Monitor the dashboard:" -ForegroundColor Yellow
Write-Host "  streamlit run frontend/dashboard.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "[API] View API docs:" -ForegroundColor Yellow
Write-Host "  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
