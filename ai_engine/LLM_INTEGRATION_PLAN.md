# LLM Integration Plan - Module 2.4

## 📋 Current Status (Module 2.3)

**Answer Generation:** Rule-based, intent-specific formatting

```python
def generate_answer(query, context, intent_analysis):
    # Rule-based answer generation
    if intent == "definitional":
        answer = f"Based on {source}: {excerpt}"
    elif intent == "factual":
        answer = f"According to {act}, Section {section}: {excerpt}"
    # etc...
```

**Pros:** ✅ Fast, ✅ Predictable, ✅ No API costs
**Cons:** ❌ Not conversational, ❌ Limited synthesis, ❌ No reasoning

---

## 🚀 Module 2.4: LLM Integration

### **Goal:** Replace rule-based answer generation with LLM-powered synthesis

---

## 🎯 LLM Options

### **Option 1: Hugging Face Local Models (FREE)**

**Recommended Models:**
- `microsoft/Phi-3-mini-4k-instruct` (3.8B params, fast)
- `google/flan-t5-large` (780M params, very fast)
- `mistralai/Mistral-7B-Instruct-v0.2` (7B params, best quality)

**Pros:**
- ✅ Free (no API costs)
- ✅ Privacy (runs locally)
- ✅ No rate limits

**Cons:**
- ❌ Requires GPU for good speed (CPU possible but slow)
- ❌ Larger model size (~4-14GB)
- ❌ More setup complexity

### **Option 2: OpenAI API (PAID)**

**Models:**
- `gpt-3.5-turbo` ($0.50 per 1M tokens)
- `gpt-4o-mini` ($0.15 per 1M tokens)

**Pros:**
- ✅ Best quality
- ✅ No local compute needed
- ✅ Easy setup

**Cons:**
- ❌ Costs money
- ❌ Requires API key
- ❌ Requires internet

### **Option 3: Ollama (FREE, LOCAL)**

**Recommended for beginners:**
```bash
# Install Ollama
ollama pull llama3.2:3b

# Use in Python
import ollama
response = ollama.chat(model='llama3.2:3b', messages=[...])
```

**Pros:**
- ✅ Easy setup
- ✅ Free
- ✅ Local

**Cons:**
- ❌ Still requires decent CPU/GPU
- ❌ Additional dependency

---

## 📝 Implementation Plan

### **Step 1: Add LLM Module**

Create: `ai_engine/src/llm/generator.py`

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class LLMGenerator:
    def __init__(self, model_name="microsoft/Phi-3-mini-4k-instruct"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
    
    def generate(self, prompt, max_length=512):
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs, max_length=max_length)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
```

### **Step 2: Create Prompt Templates**

```python
LEGAL_PROMPT_TEMPLATE = """You are a legal AI assistant. Based on the following legal documents, answer the user's question accurately and concisely.

Question: {question}

Legal Documents:
{context}

Instructions:
- Cite specific sections/acts when mentioned
- Be accurate and professional
- Keep answer under 500 words
- If uncertain, say so

Answer:"""
```

### **Step 3: Update `generate_answer()` Method**

```python
def generate_answer(self, query, context, intent_analysis):
    # Build context from retrieved documents
    context_text = self._build_context_text(context)
    
    # Create prompt
    prompt = LEGAL_PROMPT_TEMPLATE.format(
        question=query,
        context=context_text
    )
    
    # Generate with LLM
    answer = self.llm_generator.generate(prompt)
    
    return answer, confidence, sources
```

### **Step 4: Add Dependencies**

```bash
pip install transformers torch accelerate bitsandbytes
```

---

## 🎨 Intent-Specific Prompts

Make prompts adaptive based on detected intent:

```python
PROMPTS = {
    "definitional": """Define the legal term based on these documents.
    Be precise and cite the source.
    
    Question: {question}
    Documents: {context}
    
    Definition:""",
    
    "comparative": """Compare the legal concepts mentioned.
    Highlight key differences clearly.
    
    Question: {question}
    Documents: {context}
    
    Comparison:""",
    
    "procedural": """Explain the procedure step-by-step.
    Be clear and actionable.
    
    Question: {question}
    Documents: {context}
    
    Procedure:"""
}
```

---

## 📊 Comparison: Rule-Based vs LLM

| Feature | Rule-Based (Current) | LLM-Powered (Module 2.4) |
|---------|---------------------|--------------------------|
| **Quality** | Basic formatting | Natural, conversational |
| **Synthesis** | Copy-paste excerpts | Synthesizes multiple sources |
| **Reasoning** | None | Can explain and reason |
| **Citations** | Simple | Smart citation integration |
| **Speed** | 1-5ms | 500-2000ms (local), 100-500ms (API) |
| **Cost** | Free | Free (local) or $0.001-0.01/query (API) |
| **Setup** | None | Moderate (local) or easy (API) |

---

## 🔧 Hybrid Approach (RECOMMENDED)

**Best of both worlds:**

```python
def generate_answer(self, query, context, intent_analysis):
    confidence = intent_analysis.confidence
    
    # Use LLM only for high-confidence, complex queries
    if confidence >= 0.7 and intent in ['comparative', 'exploratory']:
        # Use LLM for synthesis
        answer = self._llm_generate(query, context)
    else:
        # Use rule-based for simple queries (faster)
        answer = self._rule_based_generate(query, context, intent)
    
    return answer
```

**Benefits:**
- ✅ Fast for simple queries (rule-based)
- ✅ High quality for complex queries (LLM)
- ✅ Lower LLM costs
- ✅ Fallback if LLM fails

---

## 🚦 Implementation Stages

### **Stage 1: Simple LLM (Easiest)**
```python
# Use Ollama for local LLM
import ollama

response = ollama.chat(
    model='llama3.2:3b',
    messages=[{'role': 'user', 'content': prompt}]
)
answer = response['message']['content']
```

### **Stage 2: Optimized Local Model**
```python
# Use Hugging Face with optimizations
from transformers import pipeline

generator = pipeline('text-generation', model='microsoft/Phi-3-mini-4k-instruct')
answer = generator(prompt, max_length=512)[0]['generated_text']
```

### **Stage 3: Production-Ready**
```python
# OpenAI API for best quality
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}]
)
answer = response.choices[0].message.content
```

---

## 📝 Module 2.4 Checklist

- [ ] Choose LLM approach (local vs API)
- [ ] Install LLM dependencies
- [ ] Create `llm/generator.py` module
- [ ] Design prompt templates
- [ ] Integrate with `generate_answer()`
- [ ] Test answer quality
- [ ] Optimize inference speed
- [ ] Add caching for repeated queries
- [ ] Implement hybrid rule-based/LLM approach
- [ ] Benchmark performance and costs

---

## 💡 Recommendation for Your Case

Given you're building a Legal Research Assistant:

**🎯 Start with: Ollama (Free, Local)**
1. Easy to set up
2. Good quality (Llama 3.2 is excellent)
3. No costs
4. Works offline

**Then upgrade to: Hybrid Approach**
- Rule-based for definitions (fast, accurate)
- LLM for comparisons and analysis (better synthesis)

**Future: Consider OpenAI API**
- If you need best quality
- When you have budget
- For production deployment

---

## 🔗 Resources

- **Ollama:** https://ollama.ai
- **Hugging Face Models:** https://huggingface.co/models
- **LangChain (for advanced prompting):** https://python.langchain.com
- **Prompt Engineering Guide:** https://www.promptingguide.ai

---

**Module 2.4 will make answers conversational and intelligent!** 🚀

For now, Module 2.3 works excellently with rule-based generation.
