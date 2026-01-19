# AI Coding Challenges

This directory contains coding challenges designed to evaluate **human judgment when using AI coding tools**, not just AI capability.

## Philosophy

Traditional coding tests often measure whether someone can produce working code. With AI tools, nearly everyone can produce working code. These challenges instead measure:

1. **Trade-off analysis** - Can they reason about architectural decisions?
2. **Edge case identification** - Do they catch what AI misses?
3. **Incremental complexity handling** - Can they refactor when requirements evolve?
4. **Honest self-assessment** - Do they know what they don't know?

## Challenges

### 1. Architecture: Notification System

**Type**: Trade-off decision making

**Skills tested**:
- Architectural reasoning
- Trade-off analysis
- Failure mode identification
- Production readiness thinking

**Grading distribution**:
- 40% Design document (trade-offs, alternatives)
- 40% Implementation
- 20% Testing & monitoring strategy

[→ Go to challenge](./architecture-notification-system/)

---

### 2. Multi-Stage: E-Commerce Cart

**Type**: Incremental complexity

**Skills tested**:
- Building incrementally
- Handling evolving requirements
- Refactoring decisions
- Concurrency reasoning

**Grading distribution**:
- Stage 1 required for any grade
- Stage 2 required for B or higher
- Stage 3 quality determines A vs B

[→ Go to challenge](./multi-stage-cart/)

---

## Administering the Challenges

### Time Recommendations

| Challenge | Suggested Time |
|-----------|---------------|
| Notification System | 2-3 hours |
| E-Commerce Cart (all stages) | 3-4 hours |

### Environment Setup

Candidates need:
- Node.js 18+
- npm or yarn
- Their preferred AI coding tool

### Evaluation Tips

**What to look for**:
- Quality of questions asked (clarifications, edge cases)
- Trade-off reasoning in design docs
- Honesty about limitations
- Code quality AND reasoning quality

**Red flags**:
- No design reasoning, just code
- Ignoring edge cases mentioned in requirements
- Over-engineering simple parts, under-engineering complex parts
- Unable to explain their own code

### Grading Rubric Summary

| Grade | Characteristics |
|-------|----------------|
| A | Thorough trade-off analysis, catches edge cases, honest about limitations, clean code |
| B | Working solution, reasonable architecture, handles main scenarios |
| C | Basic solution works, weak reasoning, misses edge cases |
| D | Partial solution, no meaningful design discussion |
