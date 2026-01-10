# Test GraphQL Query
$query = @"
{
  "query": "query { search(query: \"What is anticipatory bail?\") { question intent answer graph_references { case_name case_year section } } }"
}
"@

Write-Host "Testing GraphQL Integration..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod `
        -Uri "http://localhost:4000/graphql" `
        -Method POST `
        -ContentType "application/json" `
        -Body $query
    
    Write-Host "`n✅ SUCCESS!" -ForegroundColor Green
    Write-Host "Intent: $($response.data.search.intent)"
    Write-Host "Graph Facts: $($response.data.search.graph_references.Count)"
    Write-Host "`nAnswer Preview:"
    Write-Host $response.data.search.answer.Substring(0, [Math]::Min(150, $response.data.search.answer.Length))
    
} catch {
    Write-Host "`n❌ Error: $_" -ForegroundColor Red
}
