# Test GraphQL After Fix
Write-Host "Testing GraphQL Integration (Fixed)..." -ForegroundColor Cyan

$query = @"
{
  "query": "query { search(query: \"What is bail?\") { question intent answer sources { content relevance_score } } }"
}
"@

try {
    $response = Invoke-RestMethod `
        -Uri "http://localhost:4000/graphql" `
        -Method POST `
        -ContentType "application/json" `
        -Body $query
    
    Write-Host "`n✅ SUCCESS! GraphQL Working!" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "Question: $($response.data.search.question)"
    Write-Host "Intent: $($response.data.search.intent)"
    Write-Host "Sources: $($response.data.search.sources.Count)"
    Write-Host "`nAnswer Preview:"
    Write-Host $response.data.search.answer.Substring(0, [Math]::Min(200, $response.data.search.answer.Length))
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
} catch {
    Write-Host "`n❌ Still failing: $_" -ForegroundColor Red
    Write-Host "Restart the backend server first!"
}
