import { Cart, Discount, SavedCart } from '../types';

/**
 * In-memory storage for the cart service
 *
 * This is provided for the challenge. You may extend it as needed.
 */
export class MemoryStore {
  private carts: Map<string, Cart> = new Map();
  private userCarts: Map<string, string[]> = new Map();  // userId -> cartIds
  private discounts: Map<string, Discount> = new Map();
  private savedCarts: Map<string, SavedCart> = new Map();
  private userSavedCarts: Map<string, string[]> = new Map();  // userId -> savedCartIds

  constructor() {
    // Pre-populate some discount codes for testing
    this.initializeDiscounts();
  }

  // ============================================
  // Cart Storage
  // ============================================

  saveCart(cart: Cart): void {
    this.carts.set(cart.id, cart);

    // Index by user
    const userCarts = this.userCarts.get(cart.userId) || [];
    if (!userCarts.includes(cart.id)) {
      userCarts.push(cart.id);
      this.userCarts.set(cart.userId, userCarts);
    }
  }

  getCart(cartId: string): Cart | undefined {
    return this.carts.get(cartId);
  }

  deleteCart(cartId: string): boolean {
    const cart = this.carts.get(cartId);
    if (!cart) return false;

    // Remove from user index
    const userCarts = this.userCarts.get(cart.userId) || [];
    const index = userCarts.indexOf(cartId);
    if (index > -1) {
      userCarts.splice(index, 1);
      this.userCarts.set(cart.userId, userCarts);
    }

    this.carts.delete(cartId);
    return true;
  }

  getCartsByUserId(userId: string): Cart[] {
    const cartIds = this.userCarts.get(userId) || [];
    return cartIds
      .map(id => this.carts.get(id))
      .filter((c): c is Cart => c !== undefined);
  }

  // ============================================
  // Discount Storage
  // ============================================

  getDiscount(code: string): Discount | undefined {
    return this.discounts.get(code.toUpperCase());
  }

  updateDiscount(discount: Discount): void {
    this.discounts.set(discount.code.toUpperCase(), discount);
  }

  private initializeDiscounts(): void {
    const now = new Date();
    const futureDate = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000); // 30 days
    const pastDate = new Date(now.getTime() - 24 * 60 * 60 * 1000); // Yesterday

    // Active discounts
    this.discounts.set('SAVE10', {
      code: 'SAVE10',
      type: 'percentage',
      value: 10,
      currentUses: 0,
      expiresAt: futureDate
    });

    this.discounts.set('FLAT500', {
      code: 'FLAT500',
      type: 'fixed_amount',
      value: 500,  // $5.00
      minCartValue: 2000,  // Minimum $20.00
      currentUses: 0,
      expiresAt: futureDate
    });

    this.discounts.set('BUY2GET1', {
      code: 'BUY2GET1',
      type: 'buy_x_get_y',
      value: 0,
      buyX: 2,
      getY: 1,
      currentUses: 0,
      expiresAt: futureDate
    });

    this.discounts.set('VIP20', {
      code: 'VIP20',
      type: 'percentage',
      value: 20,
      maxUses: 100,
      currentUses: 99,  // Almost exhausted
      expiresAt: futureDate
    });

    // Expired discount (for testing)
    this.discounts.set('EXPIRED', {
      code: 'EXPIRED',
      type: 'percentage',
      value: 50,
      currentUses: 0,
      expiresAt: pastDate
    });
  }

  // ============================================
  // Saved Cart Storage (Stage 3)
  // ============================================

  saveSavedCart(savedCart: SavedCart): void {
    this.savedCarts.set(savedCart.id, savedCart);

    const userSaved = this.userSavedCarts.get(savedCart.userId) || [];
    userSaved.push(savedCart.id);
    this.userSavedCarts.set(savedCart.userId, userSaved);
  }

  getSavedCart(savedCartId: string): SavedCart | undefined {
    return this.savedCarts.get(savedCartId);
  }

  getSavedCartsByUserId(userId: string): SavedCart[] {
    const savedIds = this.userSavedCarts.get(userId) || [];
    return savedIds
      .map(id => this.savedCarts.get(id))
      .filter((sc): sc is SavedCart => sc !== undefined);
  }

  deleteSavedCart(savedCartId: string): boolean {
    const savedCart = this.savedCarts.get(savedCartId);
    if (!savedCart) return false;

    const userSaved = this.userSavedCarts.get(savedCart.userId) || [];
    const index = userSaved.indexOf(savedCartId);
    if (index > -1) {
      userSaved.splice(index, 1);
      this.userSavedCarts.set(savedCart.userId, userSaved);
    }

    this.savedCarts.delete(savedCartId);
    return true;
  }

  // ============================================
  // Utility
  // ============================================

  clear(): void {
    this.carts.clear();
    this.userCarts.clear();
    this.savedCarts.clear();
    this.userSavedCarts.clear();
    this.initializeDiscounts();
  }
}
