# Problem 2: E-Commerce Shopping Cart (Multi-Stage)

This challenge tests your ability to build incrementally complex features while managing technical debt and making good architectural decisions.

## Overview

You'll build a shopping cart service in **three stages**. Each stage adds complexity and may require refactoring previous work.

**Grading:**
- Must pass Stage 1 to receive any grade
- Stage 2 completion required for B or higher
- Stage 3 quality determines A vs B

---

## Stage 1: Basic Cart (Entry Level)

### Requirements

Build a REST API for a shopping cart service:

| Endpoint | Description |
|----------|-------------|
| `POST /carts` | Create a new cart for a user |
| `GET /carts/:cartId` | Get cart contents |
| `POST /carts/:cartId/items` | Add item to cart |
| `PATCH /carts/:cartId/items/:productId` | Update item quantity |
| `DELETE /carts/:cartId/items/:productId` | Remove item from cart |
| `DELETE /carts/:cartId` | Clear/delete cart |

### Data Model

```typescript
interface CartItem {
  productId: string;
  name: string;
  price: number;      // Price in cents
  quantity: number;
}

interface Cart {
  id: string;
  userId: string;
  items: CartItem[];
  createdAt: Date;
  updatedAt: Date;
}
```

### Deliverables
- [ ] Working API with all endpoints
- [ ] Basic input validation
- [ ] Tests passing: `npm test -- --grep "Stage 1"`

---

## Stage 2: Inventory & Pricing (Intermediate)

**Read this section only after completing Stage 1**

### New Requirements

#### 2.1 Inventory Integration

An inventory service is now provided (see `src/mocks/inventory.service.ts`).

- Before adding to cart, check available inventory
- Handle: User requests quantity > available stock
- Handle: Item in cart becomes unavailable (inventory drops to 0)
- Endpoint: `POST /carts/:cartId/validate` - Check all items still available

#### 2.2 Discount Codes

Support discount codes with the following types:
- `percentage` - X% off entire cart
- `fixed_amount` - $X off entire cart
- `buy_x_get_y` - Buy X items, get Y free (cheapest items free)

Discount rules:
- Discounts can have minimum cart value requirement
- Discounts can have expiration dates
- Only one discount code per cart

| Endpoint | Description |
|----------|-------------|
| `POST /carts/:cartId/discount` | Apply discount code |
| `DELETE /carts/:cartId/discount` | Remove discount code |

Cart response should now include:
```typescript
interface Cart {
  // ... existing fields
  subtotal: number;           // Sum of (price * quantity)
  discount?: {
    code: string;
    type: string;
    amount: number;           // Discount amount in cents
  };
  total: number;              // subtotal - discount
}
```

#### 2.3 Cart Expiration

- Carts inactive for 30 minutes should be marked as expired
- Expired carts cannot be modified
- `POST /carts/:cartId/refresh` - Extend cart lifetime by 30 minutes

### Deliverables
- [ ] Inventory checking on add/update
- [ ] Discount code support
- [ ] Cart expiration logic
- [ ] Tests passing: `npm test -- --grep "Stage 2"`

---

## Stage 3: Multi-Region & Collaboration (Advanced)

**Read this section only after completing Stage 2**

### New Requirements

#### 3.1 Multi-Currency Support

An exchange rate service is provided (see `src/mocks/exchange-rate.service.ts`).

- Users can view cart in different currencies
- `GET /carts/:cartId?currency=EUR` - View cart in specified currency
- All amounts shown in requested currency
- Original prices stored in USD (cents)

#### 3.2 Shared Carts

Multiple users can collaborate on a single cart:

| Endpoint | Description |
|----------|-------------|
| `POST /carts/:cartId/collaborators` | Invite user by email |
| `DELETE /carts/:cartId/collaborators/:userId` | Remove collaborator |
| `GET /carts/:cartId/collaborators` | List collaborators |

Rules:
- Cart owner can invite collaborators
- Collaborators can add/remove items but NOT checkout or delete cart
- Handle concurrent modifications (two users modify at same time)

#### 3.3 Saved Carts & Wishlists

| Endpoint | Description |
|----------|-------------|
| `POST /carts/:cartId/save` | Save cart as named list |
| `GET /users/:userId/saved-carts` | Get user's saved carts |
| `POST /carts/:cartId/restore/:savedCartId` | Restore a saved cart |

Restore modes:
- `merge` - Add saved items to current cart
- `replace` - Replace current cart with saved items

Handle: Saved cart references products that no longer exist

#### 3.4 Checkout Preparation

| Endpoint | Description |
|----------|-------------|
| `POST /carts/:cartId/checkout` | Initiate checkout |
| `DELETE /carts/:cartId/checkout` | Cancel checkout |

Checkout process:
1. Validate all items available at current prices
2. Lock cart during checkout (5-minute timeout)
3. Lock in exchange rate if viewing in non-USD currency
4. Return detailed errors if validation fails:

```typescript
interface CheckoutValidation {
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
  exchangeRate?: { from: string; to: string; rate: number; };
}
```

### Deliverables
- [ ] Multi-currency support
- [ ] Collaborative carts with conflict handling
- [ ] Save/restore functionality
- [ ] Checkout validation and locking
- [ ] Write-up: How did you handle concurrent modifications?
- [ ] Write-up: What would break at 10,000 checkouts/minute?
- [ ] Tests passing: `npm test -- --grep "Stage 3"`

---

## Getting Started

```bash
npm install
npm run dev      # Start development server on port 3001
npm test         # Run all tests
npm test -- --grep "Stage 1"   # Run only Stage 1 tests
```

## Project Structure

```
src/
├── index.ts                    # Application entry point
├── types.ts                    # TypeScript interfaces (all stages)
├── routes/
│   └── cart.routes.ts          # API routes (implement here)
├── services/
│   └── cart.service.ts         # Core logic (implement here)
├── storage/
│   └── memory.store.ts         # In-memory storage
└── mocks/
    ├── inventory.service.ts    # Mock inventory (Stage 2+)
    ├── exchange-rate.service.ts # Mock exchange rates (Stage 3)
    └── products.ts             # Sample product data
```

## Grading Rubric

| Stage | A | B | C |
|-------|---|---|---|
| 1 | Clean API design, proper error handling, good validation | Working API, reasonable structure | Works but messy code |
| 2 | All edge cases handled, clear inventory strategy, proper discount logic | Most cases handled, minor gaps | Happy path works, edge cases fail |
| 3 | Solid concurrency approach, honest trade-off analysis, clean refactoring | Working solution, some race conditions | Features bolted on, obvious race conditions |
