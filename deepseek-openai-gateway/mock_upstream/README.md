
# Mock DeepSeek SSE Upstream Service

This directory contains a **mock DeepSeek Chat Completion SSE server** used for local testing of the DeepSeek → OpenAI Gateway challenge.

It simulates:

* normal token streaming
* HTTP 429 rate limit errors
* mid-stream disconnect errors (connection drop)

> This upstream is **not** the solution; it only simulates the provider that your gateway talks to.

---

## 🚀 1. Install Dependencies

In this folder:

```bash
pip install -r requirements.txt
```

`requirements.txt` should contain:

```
fastapi
uvicorn
```

---

## ▶️ 2. Run the Mock Upstream Server

Start the server on port **9001**:

```bash
uvicorn mock_deepseek_sse:app --host 0.0.0.0 --port 9001 --reload
```

You should see:

```
Mock DeepSeek SSE upstream is running
```

Now your upstream base URL is:

```
http://localhost:9001
```

Your gateway must connect to:

```
POST http://localhost:9001/v1/chat/completions
```

Set this in your gateway environment:

```bash
export UPSTREAM_BASE_URL=http://localhost:9001
```

---

## 🧪 3. Test the Mock Server Directly (Optional)

### Normal streaming

```bash
curl -N http://localhost:9001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true,
    "test_mode": "normal"
  }'
```

You should see multiple SSE chunks ending with:

```
data: [DONE]
```

---

### Rate limit error (HTTP 429)

```bash
curl -i http://localhost:9001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true,
    "test_mode": "rate_limit"
  }'
```

---

### Mid-stream connection drop

```bash
curl -N http://localhost:9001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true,
    "test_mode": "stream_error"
  }'
```

Your gateway must convert this into a downstream:

```
event: response.error
data: {"type":"upstream_stream_broken", ...}
```

---

## 📂 4. File Structure

```
mock_upstream/
  mock_deepseek_sse.py    ← the SSE server
  README.md               ← this file
  requirements.txt        ← dependencies
```

---

## ✔ 5. Notes for Students

* You **do not** need to modify this server.
* Your gateway connects to it exactly like a real DeepSeek endpoint.
* Your gateway should handle streaming, mapping, and errors as described in the main problem spec.

---


