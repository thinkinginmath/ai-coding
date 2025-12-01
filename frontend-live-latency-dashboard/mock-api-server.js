#!/usr/bin/env node
/**
 * Mock API server for frontend-live-latency-dashboard testing.
 *
 * This server provides controlled data for automated testing.
 * It can operate in different modes:
 *   - random: Returns random latency data (default)
 *   - test: Returns predictable sequences for testing
 *   - spike: Returns data with intentional spikes
 *   - error: Simulates server errors
 *
 * Usage:
 *   node mock-api-server.js [--mode=test] [--port=3001]
 */

const http = require('http');
const url = require('url');

// Configuration
const DEFAULT_PORT = 3001;
const DEFAULT_MODE = 'random';

// Parse command line arguments
const args = process.argv.slice(2);
let mode = DEFAULT_MODE;
let port = DEFAULT_PORT;
let errorRate = 0; // Probability of returning 500 error

for (const arg of args) {
  if (arg.startsWith('--mode=')) {
    mode = arg.split('=')[1];
  } else if (arg.startsWith('--port=')) {
    port = parseInt(arg.split('=')[1]);
  } else if (arg.startsWith('--error-rate=')) {
    errorRate = parseFloat(arg.split('=')[1]);
  }
}

// State for test mode
let requestCount = 0;

/**
 * Generate latency data based on mode.
 */
function generateLatencyData(mode, count = 60) {
  const now = Math.floor(Date.now() / 1000);
  const data = [];

  switch (mode) {
    case 'test':
      // Predictable sequence for testing
      // Pattern: mostly 100-150ms with occasional spikes to 350ms
      for (let i = 0; i < count; i++) {
        const ts = now - (count - i);
        let latency;

        if (i === 10 || i === 30 || i === 50) {
          latency = 350; // Spike above threshold
        } else if (i % 5 === 0) {
          latency = 200;
        } else {
          latency = 120 + (i % 20);
        }

        data.push({ ts, latency });
      }
      break;

    case 'spike':
      // Guaranteed spike for alert testing
      for (let i = 0; i < count; i++) {
        const ts = now - (count - i);
        const latency = i === count - 1 ? 400 : 120 + Math.random() * 30;
        data.push({ ts, latency: Math.round(latency) });
      }
      break;

    case 'no-spike':
      // All values below 300
      for (let i = 0; i < count; i++) {
        const ts = now - (count - i);
        const latency = 150 + Math.random() * 100; // 150-250ms
        data.push({ ts, latency: Math.round(latency) });
      }
      break;

    case 'random':
    default:
      // Random realistic latency data
      for (let i = 0; i < count; i++) {
        const ts = now - (count - i);
        let latency = 100 + Math.random() * 150; // Base 100-250ms

        // Occasional spikes
        if (Math.random() < 0.1) {
          latency += Math.random() * 200; // Spike up to 450ms
        }

        data.push({ ts, latency: Math.round(latency) });
      }
      break;
  }

  return data;
}

/**
 * Handle CORS preflight requests
 */
function handleCORS(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

/**
 * Main request handler
 */
const server = http.createServer((req, res) => {
  handleCORS(res);

  // Handle OPTIONS (CORS preflight)
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;

  // Health check endpoint
  if (pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', mode }));
    return;
  }

  // Main metrics endpoint
  if (pathname === '/metrics/latency' && req.method === 'GET') {
    requestCount++;

    // Simulate random errors if error-rate is set
    if (errorRate > 0 && Math.random() < errorRate) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Internal server error' }));
      console.log(`[${new Date().toISOString()}] GET /metrics/latency -> 500 (simulated error)`);
      return;
    }

    // Generate data
    const data = generateLatencyData(mode);

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(data));

    console.log(`[${new Date().toISOString()}] GET /metrics/latency -> 200 (${data.length} points, mode=${mode})`);
    return;
  }

  // Special endpoint for test mode control
  if (pathname === '/test/set-mode' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        const { newMode } = JSON.parse(body);
        mode = newMode || mode;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ mode }));
        console.log(`[${new Date().toISOString()}] Mode changed to: ${mode}`);
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
      }
    });
    return;
  }

  // 404 for unknown paths
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found' }));
});

server.listen(port, () => {
  console.log('='.repeat(70));
  console.log('Mock API Server for Frontend Dashboard Testing');
  console.log('='.repeat(70));
  console.log(`Server running at http://localhost:${port}`);
  console.log(`Mode: ${mode}`);
  console.log(`Error rate: ${errorRate * 100}%`);
  console.log('');
  console.log('Available endpoints:');
  console.log(`  GET  http://localhost:${port}/metrics/latency`);
  console.log(`  GET  http://localhost:${port}/health`);
  console.log(`  POST http://localhost:${port}/test/set-mode`);
  console.log('');
  console.log('Available modes: random, test, spike, no-spike');
  console.log('Press Ctrl+C to stop');
  console.log('='.repeat(70));
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\nShutting down mock API server...');
  console.log(`Total requests served: ${requestCount}`);
  server.close();
  process.exit(0);
});
