import { IExchangeRateService, ExchangeRate } from '../types';

/**
 * Mock Exchange Rate Service
 *
 * Simulates a currency exchange rate API.
 * Rates are relative to USD (base currency).
 *
 * DO NOT MODIFY - This simulates an external service
 */
export class MockExchangeRateService implements IExchangeRateService {
  // Exchange rates relative to USD
  private rates: Map<string, number> = new Map([
    ['USD', 1.0],
    ['EUR', 0.92],
    ['GBP', 0.79],
    ['JPY', 149.50],
    ['CAD', 1.36],
    ['AUD', 1.53],
    ['CNY', 7.24],
    ['INR', 83.12],
    ['MXN', 17.15],
    ['BRL', 4.97],
  ]);

  // Track when rates were last "updated" for realistic behavior
  private lastUpdate: Date = new Date();

  // Simulate rate fluctuation
  private fluctuationEnabled: boolean = false;

  async getRate(from: string, to: string): Promise<ExchangeRate> {
    await this.simulateLatency();

    const fromRate = this.rates.get(from.toUpperCase());
    const toRate = this.rates.get(to.toUpperCase());

    if (fromRate === undefined) {
      throw new Error(`Unsupported currency: ${from}`);
    }
    if (toRate === undefined) {
      throw new Error(`Unsupported currency: ${to}`);
    }

    // Calculate cross rate
    let rate = toRate / fromRate;

    // Apply small random fluctuation if enabled (simulates real market)
    if (this.fluctuationEnabled) {
      const fluctuation = 1 + (Math.random() - 0.5) * 0.02; // ±1%
      rate *= fluctuation;
    }

    return {
      from: from.toUpperCase(),
      to: to.toUpperCase(),
      rate: Math.round(rate * 10000) / 10000, // 4 decimal places
      timestamp: new Date()
    };
  }

  getSupportedCurrencies(): string[] {
    return Array.from(this.rates.keys());
  }

  // ============================================
  // Test Helpers
  // ============================================

  // Enable rate fluctuation for testing exchange rate locking
  enableFluctuation(): void {
    this.fluctuationEnabled = true;
  }

  // Disable rate fluctuation
  disableFluctuation(): void {
    this.fluctuationEnabled = false;
  }

  // Set a specific rate for testing
  setRate(currency: string, rateToUsd: number): void {
    this.rates.set(currency.toUpperCase(), rateToUsd);
  }

  // Simulate a major rate change (for testing checkout validation)
  simulateMajorRateChange(currency: string, changePercent: number): void {
    const currentRate = this.rates.get(currency.toUpperCase());
    if (currentRate) {
      this.rates.set(currency.toUpperCase(), currentRate * (1 + changePercent / 100));
    }
  }

  // Reset to default rates
  reset(): void {
    this.rates.clear();
    this.rates.set('USD', 1.0);
    this.rates.set('EUR', 0.92);
    this.rates.set('GBP', 0.79);
    this.rates.set('JPY', 149.50);
    this.rates.set('CAD', 1.36);
    this.rates.set('AUD', 1.53);
    this.rates.set('CNY', 7.24);
    this.rates.set('INR', 83.12);
    this.rates.set('MXN', 17.15);
    this.rates.set('BRL', 4.97);
    this.fluctuationEnabled = false;
  }

  private simulateLatency(): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, 20));
  }
}
