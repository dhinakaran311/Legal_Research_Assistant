# Quick GraphQL Test
$body = @{
    query = @"
    query {
      search(query: "What is bail?") {
        question
        intent
        answer
      }
    }
"@
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "http://localhost:4000/graphql" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body `
    -UseBasicParsing

Write-Host "Status: $($response.StatusCode)"
Write-Host "Response:"
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
