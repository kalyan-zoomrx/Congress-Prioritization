# Rule Analysis Evaluator - Metrics Documentation

## 1. SYNTACTIC EVALUATION

### Test Case 1.1 Schema Validation
**Checks:**
- Presence of `relevance_rule` object
- Presence of `priority_rules` array
- Required fields in relevance_rule: `rule_text`, `approach`, `key_concepts`, `reasoning`
- Required fields in priority_rule: `priority`, `rule_text`, `approach`, `key_concepts`, `exclusions`, `reasoning`
- Required fields in key_concepts: `keywords`, `categories`, `contextual_concepts`

---

### Test Case 1.2 Completeness
**Checks:**
- All priority levels present (Very High, High, Internal, Medium, Low) by retrieving the priority levels from `rules.csv`
- All client given keywords should be in Relevance Rule `key_concepts.keywords`
- `approach` field should have `keyword` or `contextual` or `hybrid`
- Keywords exist in all rules
- Categories assigned [Might be Empty]
- Exclusions defined [Might be Empty]

---

## 2. SEMANTIC EVALUATION (25% weight each)

### Test Case 2.1 Rule Logic
**Checks:**
- Priority hierarchy order (Very High → High → Internal → Medium → Low)
- Mutual Exclusivity and Exclusion Analysis through LLM

[Human in loop will be another step of evaluation]

---