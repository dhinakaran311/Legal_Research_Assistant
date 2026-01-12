# How to Enable LLM (Ollama) in Your Legal Assistant

## ✅ Good News: Ollama is Running!

Your Ollama server is running and has these models available:
- ✅ `llama3.2:3b` (default model)
- ✅ `mistral:latest`
- ✅ `llama2:latest`

## Why `use_llm` is False by Default

The system defaults to `use_llm: false` because:
1. **Rule-based is faster** (1-5ms vs 500-2000ms)
2. **Works without Ollama** (no dependency)
3. **Sufficient for testing** (good enough quality)

But now that Ollama is running, you can enable LLM!

## How to Enable LLM

### Option 1: Frontend UI (Easiest)

1. **Open Frontend:** http://localhost:3000
2. **Login/Signup** if needed
3. **Go to Search Page**
4. **Look for LLM Toggle:** There should be a checkbox or toggle for "Use LLM" or "Enable AI"
5. **Check the box** before searching
6. **Search:** Enter your query (e.g., "What is anticipatory bail?")
7. **Results will use LLM** for answer generation

### Option 2: GraphQL Playground (Direct)

1. **Open GraphQL Playground:** http://localhost:4000/graphql
2. **Run this query with `use_llm: true`:**

```graphql
query SearchTest {
  search(query: "What is anticipatory bail?", use_llm: true) {
    question
    answer
    sources {
      content
      metadata {
        act
        section
        title
      }
    }
    graph_references {
      section
      section_title
      act_name
    }
    confidence
    processing_time_ms
  }
}
```

**Key difference:** `use_llm: true` instead of `use_llm: false`

### Option 3: API Call (Programmatic)

```javascript
// In your code
const result = await callAIEngine("What is anticipatory bail?", true);
//                                                              ^^^^
//                                                          use_llm = true
```

## What Changes When LLM is Enabled?

### Rule-Based (`use_llm: false`):
```
Answer: "According to CrPC Section 438: [direct excerpt from document]"
```

### LLM-Powered (`use_llm: true`):
```
Answer: "Anticipatory bail, as defined in Section 438 of the Code of Criminal 
Procedure, 1973, allows a person who apprehends arrest for a non-bailable 
offence to seek bail before actually being arrested. This provision enables 
individuals to approach the High Court or Court of Session for protection 
against potential arrest..."
```

**Benefits:**
- ✅ More natural, conversational answers
- ✅ Better synthesis of multiple sources
- ✅ Explains concepts clearly
- ✅ Better for complex queries

**Trade-offs:**
- ⚠️ Slower (500-2000ms vs 1-5ms)
- ⚠️ Requires Ollama running
- ⚠️ Uses more CPU/GPU resources

## Verify LLM is Working

### Check AI Engine Logs (Terminal 1):

When LLM is enabled, you should see:
```
INFO: Initializing Ollama generator with model: llama3.2:3b
INFO: ✅ Ollama is healthy, model llama3.2:3b is available
INFO: Generating with Ollama, prompt length: 1234 chars
INFO: ✅ Generated 456 chars in 1.23s
```

### Check Response Time:

- **Rule-based:** `processing_time_ms: 50-200`
- **LLM-powered:** `processing_time_ms: 500-2000`

### Check Answer Quality:

- **Rule-based:** Direct excerpts, simple formatting
- **LLM-powered:** Natural language, synthesized, explanatory

## Troubleshooting

### If LLM doesn't work:

1. **Check Ollama is running:**
   ```powershell
   # Should return list of models
   curl http://localhost:11434/api/tags
   ```

2. **Check AI Engine logs:**
   - Look for "Ollama health check failed"
   - Look for connection errors
   - Check if model name matches

3. **Verify model is available:**
   ```powershell
   ollama list
   # Should show llama3.2:3b
   ```

4. **Check frontend checkbox:**
   - Make sure `useLlm` state is `true`
   - Check browser console for errors

5. **Test directly via GraphQL:**
   - Use GraphQL Playground
   - Set `use_llm: true` explicitly
   - Check response

## Recommended Usage

### Use Rule-Based (`use_llm: false`) for:
- ✅ Quick testing
- ✅ Simple factual queries
- ✅ Fast responses needed
- ✅ Development/debugging

### Use LLM (`use_llm: true`) for:
- ✅ Production user queries
- ✅ Complex questions needing synthesis
- ✅ Better user experience
- ✅ When quality matters more than speed

## Hybrid Approach (Future Enhancement)

The system could automatically choose:
- **Simple queries** → Rule-based (fast)
- **Complex queries** → LLM (quality)

This is planned but not yet implemented.

---

## Summary

**Your Ollama is ready!** Just set `use_llm: true` in your queries to enable LLM-powered answers.

**Quick Test:**
1. Open http://localhost:4000/graphql
2. Run query with `use_llm: true`
3. Compare answer quality with `use_llm: false`

You should see more natural, synthesized answers when LLM is enabled!
