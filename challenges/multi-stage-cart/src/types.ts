// ============================================
// Stage 1: Basic Cart Types
// ============================================

export interface CartItem {
  productId: string;
  name: string;
  price: number;      // Price in cents (USD)
  quantity: number;
}

export interface Cart {
  id: string;
  userId: string;
  items: CartItem[];
  createdAt: Date;
  updatedAt: Date;

  // Stage 2 additions
  subtotal?: number;
  discount?: AppliedDiscount;
  total?: number;
  expiresAt?: Date;

  // Stage 3 additions
  collaborators?: string[];
  ownerId?: string;
  checkoutLock?: CheckoutLock;
}

export interface AddItemRequest {
  productId: string;
  quantity: number;
}

export interface UpdateQuantityRequest {
  quantity: number;
}

// ============================================
// Stage 2: Inventory & Pricing Types
// ============================================

export interface Product {
  id: string;
  name: string;
  price: number;      // Price in cents (USD)
  description?: string;
}

export interface InventoryItem {
  productId: string;
  available: number;
  reserved: number;
}

export type DiscountType = 'percentage' | 'fixed_amount' | 'buy_x_get_y';

export interface Discount {
  code: string;
  type: DiscountType;
  value: number;                  // Percentage (0-100) or amount in cents
  minCartValue?: number;          // Minimum cart value in cents
  maxUses?: number;
  currentUses: number;
  expiresAt?: Date;
  buyX?: number;                  // For buy_x_get_y
  getY?: number;                  // For buy_x_get_y
}

export interface AppliedDiscount {
  code: string;
  type: DiscountType;
  amount: number;                 // Calculated discount amount in cents
}

export interface CartValidation {
  valid: boolean;
  issues: Array<{
    productId: string;
    issue: 'out_of_stock' | 'insufficient_stock' | 'price_changed';
    requested: number;
    available: number;
  }>;
}

// ============================================
// Stage 3: Multi-Region & Collaboration Types
// ============================================

export interface ExchangeRate {
  from: string;
  to: string;
  rate: number;
  timestamp: Date;
}

export interface Collaborator {
  userId: string;
  email: string;
  addedAt: Date;
  addedBy: string;
}

export interface SavedCart {
  id: string;
  userId: string;
  name: string;
  items: CartItem[];
  savedAt: Date;
}

export type RestoreMode = 'merge' | 'replace';

export interface CheckoutLock {
  lockedAt: Date;
  lockedUntil: Date;
  exchangeRate?: ExchangeRate;
}

export interface CheckoutValidation {
  valid: boolean;
  errors?: Array<{
    productId: string;
    issue: 'out_of_stock' | 'insufficient_stock' | 'price_changed';
    details: {
      requested?: number;
      available?: number;
      oldPrice?: number;
      newPrice?: number;
    };
  }>;
  lockedUntil?: Date;
  exchangeRate?: ExchangeRate;
}

// ============================================
// Service Interfaces
// ============================================

export interface IInventoryService {
  getAvailable(productId: string): Promise<number>;
  reserve(productId: string, quantity: number): Promise<boolean>;
  release(productId: string, quantity: number): Promise<void>;
  checkBatch(productIds: string[]): Promise<Map<string, number>>;
}

export interface IExchangeRateService {
  getRate(from: string, to: string): Promise<ExchangeRate>;
  getSupportedCurrencies(): string[];
}

export interface IProductService {
  getProduct(productId: string): Promise<Product | null>;
  getProducts(productIds: string[]): Promise<Map<string, Product>>;
}
