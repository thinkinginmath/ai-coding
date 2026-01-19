import { IInventoryService } from '../types';

/**
 * Mock Inventory Service
 *
 * Simulates an inventory management system.
 *
 * DO NOT MODIFY - This simulates an external service
 */
export class MockInventoryService implements IInventoryService {
  // Initial inventory levels
  private inventory: Map<string, { available: number; reserved: number }> = new Map([
    ['prod_001', { available: 100, reserved: 0 }],
    ['prod_002', { available: 50, reserved: 0 }],
    ['prod_003', { available: 25, reserved: 0 }],
    ['prod_004', { available: 10, reserved: 0 }],
    ['prod_005', { available: 75, reserved: 0 }],
    ['prod_006', { available: 200, reserved: 0 }],
    ['prod_007', { available: 150, reserved: 0 }],
    ['prod_008', { available: 80, reserved: 0 }],
    ['prod_009', { available: 60, reserved: 0 }],
    ['prod_010', { available: 300, reserved: 0 }],
    // Low stock item for testing
    ['prod_low_stock', { available: 2, reserved: 0 }],
    // Out of stock item for testing
    ['prod_out_of_stock', { available: 0, reserved: 0 }],
  ]);

  async getAvailable(productId: string): Promise<number> {
    await this.simulateLatency();

    const item = this.inventory.get(productId);
    if (!item) return 0;

    return item.available - item.reserved;
  }

  async reserve(productId: string, quantity: number): Promise<boolean> {
    await this.simulateLatency();

    const item = this.inventory.get(productId);
    if (!item) return false;

    const effectiveAvailable = item.available - item.reserved;
    if (effectiveAvailable < quantity) return false;

    item.reserved += quantity;
    return true;
  }

  async release(productId: string, quantity: number): Promise<void> {
    await this.simulateLatency();

    const item = this.inventory.get(productId);
    if (!item) return;

    item.reserved = Math.max(0, item.reserved - quantity);
  }

  async checkBatch(productIds: string[]): Promise<Map<string, number>> {
    await this.simulateLatency();

    const result = new Map<string, number>();
    for (const productId of productIds) {
      const item = this.inventory.get(productId);
      result.set(productId, item ? item.available - item.reserved : 0);
    }
    return result;
  }

  // ============================================
  // Test Helpers - Use these in tests
  // ============================================

  // Set inventory level for a product
  setInventory(productId: string, available: number): void {
    const existing = this.inventory.get(productId);
    this.inventory.set(productId, {
      available,
      reserved: existing?.reserved || 0
    });
  }

  // Get current inventory state (for assertions)
  getInventoryState(productId: string): { available: number; reserved: number } | undefined {
    return this.inventory.get(productId);
  }

  // Reset all inventory to initial state
  reset(): void {
    this.inventory.clear();
    this.inventory.set('prod_001', { available: 100, reserved: 0 });
    this.inventory.set('prod_002', { available: 50, reserved: 0 });
    this.inventory.set('prod_003', { available: 25, reserved: 0 });
    this.inventory.set('prod_004', { available: 10, reserved: 0 });
    this.inventory.set('prod_005', { available: 75, reserved: 0 });
    this.inventory.set('prod_006', { available: 200, reserved: 0 });
    this.inventory.set('prod_007', { available: 150, reserved: 0 });
    this.inventory.set('prod_008', { available: 80, reserved: 0 });
    this.inventory.set('prod_009', { available: 60, reserved: 0 });
    this.inventory.set('prod_010', { available: 300, reserved: 0 });
    this.inventory.set('prod_low_stock', { available: 2, reserved: 0 });
    this.inventory.set('prod_out_of_stock', { available: 0, reserved: 0 });
  }

  // Simulate a sudden stock depletion (for testing edge cases)
  depleteStock(productId: string): void {
    const item = this.inventory.get(productId);
    if (item) {
      item.available = 0;
    }
  }

  private simulateLatency(): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, 5));
  }
}
