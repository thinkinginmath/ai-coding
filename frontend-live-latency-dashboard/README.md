#Frontend Challenge — Live API Latency Dashboard

## Overview

Your task is to build a **live-updating latency dashboard** using React.

You will consume a mock backend API:

```
GET /metrics/latency
```

which returns an array of objects:

```json
[
  { "ts": 1718345000, "latency": 120 },
  { "ts": 1718345001, "latency": 118 },
  ...
]
```

A new dataset will be returned on every request.

---

## Requirements

### 1. Show the latest average latency

Render to DOM:

```html
<div data-testid="avg-latency">...</div>
```

### 2. Show the max latency

```html
<div data-testid="max-latency">...</div>
```

### 3. Poll every 5 seconds

Fetch `/metrics/latency` on mount, then every 5 seconds.

### 4. Sparkline-style chart

Use any charting method.

The DOM element **must** exist:

```html
<div data-testid="chart">
  <!-- 1 DOM element per data point -->
</div>
```

Grading checks the count of children, not graphics.

### 5. Latency spike alert

If **max latency > 300**, display:

```html
<div data-testid="alert">Latency spike detected</div>
```

Otherwise, **do not render** the alert div.

---

## Allowed Tools

* React (CRA/Vite/Next.js)
* Any chart library OR custom SVG
* Fetch, Axios, SWR, TanStack Query, etc.

---

## What We Will Test

Using automated DOM tests:

* Correct values in `avg-latency`
* Correct values in `max-latency`
* `alert` appears only for spikes
* Correct number of sparkline points
* Polling runs every 5 seconds

---

## Submission

Submit a runnable React project with a `README` describing:

* How to install
* How to run
* Any notes for the reviewer

