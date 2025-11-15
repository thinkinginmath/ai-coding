
# AI Coding Challenge Collection

This repository contains several **independent coding challenges** designed for evaluating candidates in backend, protocol engineering, systems, and frontend roles.

These challenges are organized by directory.
Each folder contains its own problem statement (`README.md`) and supporting files.

> **Note:** This top-level README is *not* part of what students receive during the test.
> Individual challenge folders include their own instructions.

---

## 📂 Challenge List

### **1. deepseek-openai-gateway/**

**Category:** Backend / API Gateway / Streaming SSE
**Skills Tested:**

* SSE parsing and transformation
* Protocol adaptation (DeepSeek → OpenAI)
* Error handling (mid-stream drop, HTTP errors)
* Streaming correctness & state machine reasoning
* Using AI tools to accelerate coding

Includes a mock upstream server to simulate DeepSeek SSE responses.

---

### **2. edge-proto-challenge/**

**Category:** Systems / Log Parsing / Protocol Evolution
**Skills Tested:**

* Parsing QUIC/HTTP/3 edge logs
* Handling schema evolution (v1.0 → v1.1)
* Robust error handling and forward compatibility
* Few-shot prompt engineering (AI-assisted coding)
* JSON report generation + modular design

---

### **3. frontend-live-latency-dashboard/**

**Category:** Frontend / React / Visualization
**Skills Tested:**

* React components, hooks, polling
* Latency aggregation and spike detection
* DOM correctness (avg, max, alert)
* Lightweight chart rendering
* Clean code structure




