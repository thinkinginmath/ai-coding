# Stage 3 Write-Up: E-Commerce Cart

> **Instructions**: Complete this write-up after finishing Stage 3. This is part of your Stage 3 grade.

## 1. Concurrent Modification Handling

### Problem Statement

Multiple users (owner + collaborators) can modify the same cart simultaneously. Describe the concurrency issues you identified and how you handled them.

### Identified Race Conditions

1. **Race Condition 1**:
   - Scenario:
   - Impact:

2. **Race Condition 2**:
   - Scenario:
   - Impact:

### Your Solution

<!-- Describe your approach to handling concurrent modifications -->

**Approach**:

**Implementation Details**:

```typescript
// Include relevant code snippets if helpful
```

**Trade-offs**:
- Pros:
- Cons:

### Alternative Approaches Considered

1. **Optimistic Locking**:
2. **Pessimistic Locking**:
3. **Last-Write-Wins**:
4. **CRDTs**:

---

## 2. Scaling Analysis

### Current Architecture Limitations

At 10,000 checkouts/minute, what would break?

1. **Limitation 1**:
   - Why it breaks:
   - At what threshold:

2. **Limitation 2**:
   - Why it breaks:
   - At what threshold:

3. **Limitation 3**:
   - Why it breaks:
   - At what threshold:

### Proposed Solutions for Scale

| Component | Current | At Scale | Migration Path |
|-----------|---------|----------|----------------|
| Storage | | | |
| Inventory | | | |
| Exchange Rates | | | |
| Checkout Lock | | | |

### Recommended Architecture at Scale

<!-- Describe what the architecture should look like at 10K checkouts/min -->

---

## 3. Honest Assessment

### What Worked Well

1.
2.

### What I Would Do Differently

1.
2.

### Known Issues / Technical Debt

1.
2.

### Time Spent

- Stage 1:
- Stage 2:
- Stage 3:
- Total:

---

## 4. Additional Notes

<!-- Any other considerations, edge cases you thought about, or notes for reviewers -->
