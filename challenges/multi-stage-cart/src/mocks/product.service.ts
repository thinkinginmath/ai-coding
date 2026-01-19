import { IProductService, Product } from '../types';
import { PRODUCT_MAP } from './products';

/**
 * Mock Product Service
 *
 * Simulates a product catalog service.
 *
 * DO NOT MODIFY - This simulates an external service
 */
export class MockProductService implements IProductService {
  // Simulate discontinued products
  private discontinuedProducts: Set<string> = new Set(['prod_discontinued']);

  // Simulate price changes (for testing Stage 3 checkout validation)
  private priceOverrides: Map<string, number> = new Map();

  async getProduct(productId: string): Promise<Product | null> {
    await this.simulateLatency();

    if (this.discontinuedProducts.has(productId)) {
      return null;
    }

    const product = PRODUCT_MAP.get(productId);
    if (!product) return null;

    // Apply price override if exists
    const overridePrice = this.priceOverrides.get(productId);
    if (overridePrice !== undefined) {
      return { ...product, price: overridePrice };
    }

    return product;
  }

  async getProducts(productIds: string[]): Promise<Map<string, Product>> {
    await this.simulateLatency();

    const result = new Map<string, Product>();

    for (const productId of productIds) {
      if (this.discontinuedProducts.has(productId)) {
        continue;
      }

      const product = PRODUCT_MAP.get(productId);
      if (product) {
        const overridePrice = this.priceOverrides.get(productId);
        if (overridePrice !== undefined) {
          result.set(productId, { ...product, price: overridePrice });
        } else {
          result.set(productId, product);
        }
      }
    }

    return result;
  }

  // Test helper: Simulate a price change
  setPriceOverride(productId: string, newPrice: number): void {
    this.priceOverrides.set(productId, newPrice);
  }

  // Test helper: Clear price overrides
  clearPriceOverrides(): void {
    this.priceOverrides.clear();
  }

  // Test helper: Discontinue a product
  discontinueProduct(productId: string): void {
    this.discontinuedProducts.add(productId);
  }

  // Test helper: Restore a discontinued product
  restoreProduct(productId: string): void {
    this.discontinuedProducts.delete(productId);
  }

  private simulateLatency(): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, 10));
  }
}
