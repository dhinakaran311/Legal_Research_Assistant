# 🧪 Test Queries for Multi-Act System

Sample queries to test the multi-act scraping and loading system. Use these to verify that all acts are properly loaded and searchable.

## 📋 Test Query Categories

### **1. IPC (Indian Penal Code) Queries**

Test queries for criminal law sections:

```
1. What is the punishment for murder?
   Expected: IPC Section 302

2. What is Section 302 of IPC?
   Expected: IPC Section 302 (Punishment for Murder)

3. What is the definition of murder?
   Expected: IPC Section 300

4. What is the punishment for rape?
   Expected: IPC Section 376

5. What is cheating under Indian law?
   Expected: IPC Section 420

6. What is defamation?
   Expected: IPC Section 499

7. What is criminal intimidation?
   Expected: IPC Section 506

8. What is the punishment for attempt to murder?
   Expected: IPC Section 307

9. What is cruelty against wife?
   Expected: IPC Section 498A

10. What is unnatural offence?
    Expected: IPC Section 377
```

---

### **2. CrPC (Criminal Procedure Code) Queries**

Test queries for criminal procedure:

```
1. What is anticipatory bail?
   Expected: CrPC Section 438

2. When can police arrest without warrant?
   Expected: CrPC Section 41

3. What is Section 438 of CrPC?
   Expected: CrPC Section 438 (Anticipatory Bail)

4. When can bail be granted in non-bailable offence?
   Expected: CrPC Section 437

5. What are my rights when arrested?
   Expected: CrPC Section 50, 50A

6. When should police inform about arrest?
   Expected: CrPC Section 50A

7. What is the procedure for filing FIR?
   Expected: CrPC Section 154

8. What is the power of police to investigate?
   Expected: CrPC Section 156

9. Can I get bail in bailable offences?
   Expected: CrPC Section 436

10. What is the notice before arrest?
    Expected: CrPC Section 41A
```

---

### **3. Evidence Act Queries**

Test queries for evidence law:

```
1. What is burden of proof?
   Expected: Evidence Act Section 101

2. Who has burden of proof?
   Expected: Evidence Act Section 102

3. What is estoppel?
   Expected: Evidence Act Section 115

4. What is judicial notice?
   Expected: Evidence Act Section 56, 57

5. Who can testify as witness?
   Expected: Evidence Act Section 118

6. What is privileged communication between spouses?
   Expected: Evidence Act Section 122

7. Can accomplice testimony be used?
   Expected: Evidence Act Section 133

8. What is the definition of evidence?
   Expected: Evidence Act Section 3

9. What is burden of proof for specific facts?
   Expected: Evidence Act Section 103
```

---

### **4. Contract Act Queries**

Test queries for contract law:

```
1. What are the requirements for a valid contract?
   Expected: Contract Act Section 10

2. Who is competent to contract?
   Expected: Contract Act Section 11

3. What is free consent?
   Expected: Contract Act Section 14

4. What is coercion?
   Expected: Contract Act Section 15

5. What considerations are lawful?
   Expected: Contract Act Section 23

6. What if contract becomes impossible?
   Expected: Contract Act Section 56

7. What happens to void agreements?
   Expected: Contract Act Section 65

8. What is compensation for breach of contract?
   Expected: Contract Act Section 73
```

---

### **5. CPC (Civil Procedure Code) Queries**

Test queries for civil procedure:

```
1. Which court can try civil suits?
   Expected: CPC Section 9

2. What is res judicata?
   Expected: CPC Section 11

3. What is stay of suit?
   Expected: CPC Section 10

4. Where to file civil suits?
   Expected: CPC Section 20

5. What is second appeal?
   Expected: CPC Section 100

6. When can revision be filed?
   Expected: CPC Section 115

7. What is restitution?
   Expected: CPC Section 144
```

---

### **6. Constitution Queries**

Test queries for constitutional law:

```
1. What are fundamental rights?
   Expected: Constitution Article 12-35

2. What is Article 21?
   Expected: Constitution Article 21 (Right to Life)

3. What is right to equality?
   Expected: Constitution Article 14, 15

4. What is freedom of speech?
   Expected: Constitution Article 19

5. What is right to property?
   Expected: Constitution Article 300A

6. How to enforce fundamental rights?
   Expected: Constitution Article 32, 226
```

---

### **7. Cross-Act Queries**

Test queries that should return results from multiple acts:

```
1. What is bail under criminal law?
   Expected: CrPC Section 436, 437, 438 (and possibly IPC references)

2. What are my rights if arrested?
   Expected: CrPC Section 50, 50A, 41D

3. How to prove a criminal case?
   Expected: Evidence Act Section 101-103, IPC definitions

4. What is the procedure for murder case?
   Expected: IPC Section 302, CrPC Section 154, 156

5. What are my constitutional rights during arrest?
   Expected: Constitution Article 21, 22, CrPC Section 50

6. How to prove a contract in court?
   Expected: Contract Act Section 10, Evidence Act Section 101

7. What is the punishment and procedure for cheating?
   Expected: IPC Section 420, CrPC investigation sections

8. What is bail and anticipatory bail?
   Expected: CrPC Section 436, 437, 438

9. How to file complaint for domestic violence?
   Expected: IPC Section 498A, CrPC Section 154

10. What is evidence needed for murder conviction?
    Expected: IPC Section 300, 302, Evidence Act Section 101-103
```

---

### **8. Specific Section Number Queries**

Test queries with specific section numbers:

```
1. IPC 302
   Expected: IPC Section 302 (Punishment for Murder)

2. CrPC 438
   Expected: CrPC Section 438 (Anticipatory Bail)

3. Evidence Act 101
   Expected: Evidence Act Section 101 (Burden of Proof)

4. Contract Act Section 10
   Expected: Contract Act Section 10 (Valid Contract)

5. Constitution Article 21
   Expected: Constitution Article 21 (Right to Life)

6. IPC Section 420
   Expected: IPC Section 420 (Cheating)

7. CrPC Section 41
   Expected: CrPC Section 41 (Arrest without Warrant)

8. Evidence Act Section 115
   Expected: Evidence Act Section 115 (Estoppel)
```

---

## 🎯 Testing Strategy

### **Phase 1: Single Act Testing**
Test queries for each act individually to verify:
- ✅ Data is loaded correctly
- ✅ Search returns relevant sections
- ✅ Metadata is correct

### **Phase 2: Cross-Act Testing**
Test queries that should return results from multiple acts to verify:
- ✅ Multi-act search works
- ✅ Results are relevant across acts
- ✅ Metadata distinguishes between acts

### **Phase 3: Specific Section Testing**
Test queries with specific section numbers to verify:
- ✅ Exact section matching works
- ✅ Section numbers are searchable
- ✅ Content is accurate

### **Phase 4: Real-World Scenario Testing**
Test queries based on real legal questions to verify:
- ✅ System provides practical answers
- ✅ Results are comprehensive
- ✅ Sources are credible

---

## ✅ Expected Results Format

For each query, you should see:

```json
{
  "question": "What is anticipatory bail?",
  "intent": "factual",
  "intent_confidence": 0.85,
  "answer": "Anticipatory bail is...",
  "sources": [
    {
      "content": "Section 438 content...",
      "relevance_score": 0.92,
      "metadata": {
        "act": "CrPC",
        "section": "438",
        "title": "Direction for grant of bail...",
        "category": "criminal_procedure",
        "subcategory": "bail"
      }
    }
  ],
  "graph_references": [...],
  "documents_used": 1,
  "confidence": 0.90,
  "processing_time_ms": 245.5
}
```

---

## 📝 Notes

- **Relevance:** Results should match the query intent
- **Completeness:** Should include relevant sections from appropriate acts
- **Accuracy:** Content should be correct and up-to-date
- **Metadata:** Should clearly show act, section, category
- **Performance:** Response time should be reasonable (< 2 seconds)

---

**Use these queries to thoroughly test your multi-act system!**
