/**
 * Auto-grader for frontend-live-latency-dashboard challenge.
 *
 * This Playwright test suite verifies all requirements:
 * - Correct metrics calculation (avg, max)
 * - Alert behavior based on threshold
 * - Chart rendering with correct number of elements
 * - 5-second polling interval
 * - Threshold configuration and persistence
 * - Historical data (10 minutes)
 * - Error handling
 *
 * Usage:
 *   npm test -- --reporter=json > results.json
 */

const { test, expect } = require('@playwright/test');

// Configuration
const APP_URL = process.env.APP_URL || 'http://localhost:3000';
const API_URL = process.env.API_URL || 'http://localhost:3001';
const DEFAULT_THRESHOLD = 300;

/**
 * Helper: Calculate expected average from data array
 */
function calculateAvg(data) {
  if (!data || data.length === 0) return 0;
  const sum = data.reduce((acc, item) => acc + item.latency, 0);
  return sum / data.length;
}

/**
 * Helper: Calculate expected max from data array
 */
function calculateMax(data) {
  if (!data || data.length === 0) return 0;
  return Math.max(...data.map(item => item.latency));
}

/**
 * Helper: Intercept API and return controlled data
 */
async function mockApiResponse(page, data) {
  await page.route(`${API_URL}/metrics/latency`, route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(data)
    });
  });
}

/**
 * Test Suite
 */

test.describe('Frontend Dashboard Auto-Grader', () => {

  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test
    await page.goto(APP_URL);
    await page.evaluate(() => localStorage.clear());
  });

  /**
   * TEST 1: Basic Metrics Calculation (20 points)
   */
  test('should display correct average latency', async ({ page }) => {
    const mockData = [
      { ts: 1718345000, latency: 100 },
      { ts: 1718345001, latency: 200 },
      { ts: 1718345002, latency: 150 }
    ];
    const expectedAvg = calculateAvg(mockData); // 150

    await mockApiResponse(page, mockData);
    await page.goto(APP_URL);

    // Wait for data to load
    await page.waitForTimeout(2000);

    const avgElement = page.locator('[data-testid="avg-latency"]');
    await expect(avgElement).toBeVisible();

    const avgText = await avgElement.textContent();
    const displayedAvg = parseFloat(avgText);

    expect(Math.abs(displayedAvg - expectedAvg)).toBeLessThan(0.2);
  });

  test('should display correct max latency', async ({ page }) => {
    const mockData = [
      { ts: 1718345000, latency: 100 },
      { ts: 1718345001, latency: 350 },
      { ts: 1718345002, latency: 150 }
    ];
    const expectedMax = calculateMax(mockData); // 350

    await mockApiResponse(page, mockData);
    await page.goto(APP_URL);

    await page.waitForTimeout(2000);

    const maxElement = page.locator('[data-testid="max-latency"]');
    await expect(maxElement).toBeVisible();

    const maxText = await maxElement.textContent();
    const displayedMax = parseFloat(maxText);

    expect(displayedMax).toBe(expectedMax);
  });

  /**
   * TEST 2: Alert Behavior (15 points)
   */
  test('should show alert when max latency exceeds threshold', async ({ page }) => {
    const mockData = [
      { ts: 1718345000, latency: 120 },
      { ts: 1718345001, latency: 350 }, // Above default 300
      { ts: 1718345002, latency: 140 }
    ];

    await mockApiResponse(page, mockData);
    await page.goto(APP_URL);

    await page.waitForTimeout(2000);

    const alertElement = page.locator('[data-testid="alert"]');
    await expect(alertElement).toBeVisible();

    const alertText = await alertElement.textContent();
    expect(alertText.toLowerCase()).toContain('spike');
  });

  test('should NOT show alert when max latency is below threshold', async ({ page }) => {
    const mockData = [
      { ts: 1718345000, latency: 120 },
      { ts: 1718345001, latency: 250 }, // Below 300
      { ts: 1718345002, latency: 140 }
    ];

    await mockApiResponse(page, mockData);
    await page.goto(APP_URL);

    await page.waitForTimeout(2000);

    const alertElement = page.locator('[data-testid="alert"]');
    await expect(alertElement).not.toBeVisible();
  });

  /**
   * TEST 3: Chart Rendering (15 points)
   */
  test('should render chart with correct number of data points', async ({ page }) => {
    const mockData = Array.from({ length: 20 }, (_, i) => ({
      ts: 1718345000 + i,
      latency: 120 + Math.random() * 50
    }));

    await mockApiResponse(page, mockData);
    await page.goto(APP_URL);

    await page.waitForTimeout(2000);

    const chartElement = page.locator('[data-testid="chart"]');
    await expect(chartElement).toBeVisible();

    // Count child elements (each represents a data point)
    const childCount = await chartElement.locator('*').count();

    // Should have one element per data point
    expect(childCount).toBe(mockData.length);
  });

  /**
   * TEST 4: Polling Interval (15 points)
   */
  test('should poll API every 5 seconds', async ({ page }) => {
    let requestCount = 0;
    const requestTimestamps = [];

    // Intercept and count requests
    await page.route(`${API_URL}/metrics/latency`, route => {
      requestCount++;
      requestTimestamps.push(Date.now());
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ ts: Date.now(), latency: 120 }])
      });
    });

    await page.goto(APP_URL);

    // Wait for multiple polling cycles (15 seconds = 3 requests)
    await page.waitForTimeout(16000);

    // Should have made 4 requests (initial + 3 polls)
    expect(requestCount).toBeGreaterThanOrEqual(3);
    expect(requestCount).toBeLessThanOrEqual(4);

    // Check intervals between requests
    for (let i = 1; i < requestTimestamps.length; i++) {
      const interval = requestTimestamps[i] - requestTimestamps[i - 1];
      // Should be approximately 5000ms (±500ms tolerance)
      expect(interval).toBeGreaterThan(4500);
      expect(interval).toBeLessThan(5500);
    }
  });

  /**
   * TEST 5: Threshold Configuration (20 points)
   */
  test('should initialize with default threshold in localStorage', async ({ page }) => {
    await page.goto(APP_URL);
    await page.waitForTimeout(1000);

    const threshold = await page.evaluate(() => {
      return localStorage.getItem('latencyThreshold');
    });

    expect(threshold).toBe('300');
  });

  test('should allow threshold adjustment and persist to localStorage', async ({ page }) => {
    await page.goto(APP_URL);
    await page.waitForTimeout(1000);

    // Find threshold input
    const thresholdInput = page.locator('[data-testid="threshold-input"]');
    await expect(thresholdInput).toBeVisible();

    // Change threshold to 250
    await thresholdInput.fill('250');

    // Give it time to update localStorage
    await page.waitForTimeout(500);

    // Verify localStorage updated
    const newThreshold = await page.evaluate(() => {
      return localStorage.getItem('latencyThreshold');
    });

    expect(newThreshold).toBe('250');
  });

  test('should show threshold line in chart', async ({ page }) => {
    const mockData = Array.from({ length: 10 }, (_, i) => ({
      ts: 1718345000 + i,
      latency: 100 + i * 30
    }));

    await mockApiResponse(page, mockData);
    await page.goto(APP_URL);
    await page.waitForTimeout(2000);

    // Chart should be visible
    const chartElement = page.locator('[data-testid="chart"]');
    await expect(chartElement).toBeVisible();

    // Threshold line should exist (implementation specific, but checking for common patterns)
    const hasThresholdLine = await page.evaluate(() => {
      const chart = document.querySelector('[data-testid="chart"]');
      if (!chart) return false;

      // Check for common threshold line patterns
      const hasLineElement = chart.querySelector('[data-threshold]') !== null;
      const hasSvgLine = chart.querySelector('line[data-type="threshold"]') !== null;
      const hasRefLine = chart.innerHTML.includes('threshold');

      return hasLineElement || hasSvgLine || hasRefLine;
    });

    expect(hasThresholdLine).toBe(true);
  });

  test('should highlight data points above threshold', async ({ page }) => {
    const mockData = [
      { ts: 1718345000, latency: 150 }, // Below threshold
      { ts: 1718345001, latency: 350 }, // Above threshold
      { ts: 1718345002, latency: 200 }, // Below threshold
      { ts: 1718345003, latency: 400 }  // Above threshold
    ];

    await mockApiResponse(page, mockData);
    await page.goto(APP_URL);
    await page.waitForTimeout(2000);

    // Count elements with highlighting (implementation specific)
    const highlightedCount = await page.evaluate(() => {
      const chart = document.querySelector('[data-testid="chart"]');
      if (!chart) return 0;

      // Check for common highlighting patterns
      const highlighted = chart.querySelectorAll('[data-above-threshold="true"]');
      const alertClass = chart.querySelectorAll('.alert, .spike, .warning, .danger');

      return highlighted.length || alertClass.length;
    });

    // Should have 2 highlighted points (above threshold)
    expect(highlightedCount).toBeGreaterThan(0);
  });

  test('should persist threshold across page reloads', async ({ page }) => {
    await page.goto(APP_URL);

    // Set threshold to 250
    const thresholdInput = page.locator('[data-testid="threshold-input"]');
    await thresholdInput.fill('250');
    await page.waitForTimeout(500);

    // Reload page
    await page.reload();
    await page.waitForTimeout(1000);

    // Check threshold is still 250
    const inputValue = await thresholdInput.inputValue();
    expect(inputValue).toBe('250');
  });

  /**
   * TEST 6: Historical Data (10 points)
   */
  test('should retain data from last 10 minutes', async ({ page }) => {
    const now = Math.floor(Date.now() / 1000);

    // First batch: 5 points from 11 minutes ago (should be filtered out)
    const oldData = Array.from({ length: 5 }, (_, i) => ({
      ts: now - 660 - i, // 11 minutes ago
      latency: 100
    }));

    // Second batch: 10 points from 5 minutes ago (should be retained)
    const recentData = Array.from({ length: 10 }, (_, i) => ({
      ts: now - 300 - i, // 5 minutes ago
      latency: 200
    }));

    let callCount = 0;
    await page.route(`${API_URL}/metrics/latency`, route => {
      callCount++;
      const data = callCount === 1 ? oldData : recentData;
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(data)
      });
    });

    await page.goto(APP_URL);
    await page.waitForTimeout(2000);

    // Wait for second poll
    await page.waitForTimeout(6000);

    // Chart should only show recent data (10 points, not 15)
    const chartElement = page.locator('[data-testid="chart"]');
    const childCount = await chartElement.locator('*').count();

    expect(childCount).toBe(recentData.length);
  });

  /**
   * TEST 7: Error Handling (5 points)
   */
  test('should display error message when API fails', async ({ page }) => {
    await page.route(`${API_URL}/metrics/latency`, route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    await page.goto(APP_URL);
    await page.waitForTimeout(2000);

    // Look for error message (implementation specific)
    const hasErrorMessage = await page.evaluate(() => {
      const body = document.body.textContent.toLowerCase();
      return body.includes('error') || body.includes('failed') || body.includes('unavailable');
    });

    expect(hasErrorMessage).toBe(true);
  });

  test('should continue polling after API failure', async ({ page }) => {
    let callCount = 0;

    await page.route(`${API_URL}/metrics/latency`, route => {
      callCount++;

      // First call fails
      if (callCount === 1) {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Server error' })
        });
      } else {
        // Subsequent calls succeed
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([{ ts: Date.now(), latency: 120 }])
        });
      }
    });

    await page.goto(APP_URL);

    // Wait for retry
    await page.waitForTimeout(7000);

    // Should have retried (at least 2 calls)
    expect(callCount).toBeGreaterThanOrEqual(2);
  });

});

/**
 * Score Calculation
 *
 * After running tests, calculate total score based on passed tests:
 * - Basic metrics (2 tests): 20 points
 * - Alert behavior (2 tests): 15 points
 * - Chart rendering (1 test): 15 points
 * - Polling interval (1 test): 15 points
 * - Threshold config (5 tests): 20 points
 * - Historical data (1 test): 10 points
 * - Error handling (2 tests): 5 points
 *
 * Total: 100 points
 */
