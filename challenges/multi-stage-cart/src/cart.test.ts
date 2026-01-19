import request from 'supertest';
import { app, store } from './index';
import { MockInventoryService } from './mocks/inventory.service';
import { MockProductService } from './mocks/product.service';
import { MockExchangeRateService } from './mocks/exchange-rate.service';

/**
 * Cart Service Tests
 *
 * Run specific stages:
 *   npm test -- --grep "Stage 1"
 *   npm test -- --grep "Stage 2"
 *   npm test -- --grep "Stage 3"
 */

describe('Cart Service', () => {
  beforeEach(() => {
    store.clear();
  });

  // ============================================
  // Stage 1: Basic Cart Operations
  // ============================================

  describe('Stage 1: Basic Cart Operations', () => {
    describe('POST /api/carts', () => {
      it('should create a new cart', async () => {
        const res = await request(app)
          .post('/api/carts')
          .send({ userId: 'user123' });

        expect(res.status).toBe(201);
        expect(res.body).toMatchObject({
          userId: 'user123',
          items: []
        });
        expect(res.body.id).toBeDefined();
        expect(res.body.createdAt).toBeDefined();
      });

      it('should return 400 if userId is missing', async () => {
        const res = await request(app)
          .post('/api/carts')
          .send({});

        expect(res.status).toBe(400);
      });
    });

    describe('GET /api/carts/:cartId', () => {
      it('should return cart by ID', async () => {
        // Create cart first
        const createRes = await request(app)
          .post('/api/carts')
          .send({ userId: 'user123' });

        const cartId = createRes.body.id;

        const res = await request(app).get(`/api/carts/${cartId}`);

        expect(res.status).toBe(200);
        expect(res.body.id).toBe(cartId);
      });

      it('should return 404 for non-existent cart', async () => {
        const res = await request(app).get('/api/carts/nonexistent');

        expect(res.status).toBe(404);
      });
    });

    describe('POST /api/carts/:cartId/items', () => {
      let cartId: string;

      beforeEach(async () => {
        const res = await request(app)
          .post('/api/carts')
          .send({ userId: 'user123' });
        cartId = res.body.id;
      });

      it('should add item to cart', async () => {
        const res = await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_001', quantity: 2 });

        expect(res.status).toBe(200);
        expect(res.body.items).toHaveLength(1);
        expect(res.body.items[0]).toMatchObject({
          productId: 'prod_001',
          quantity: 2,
          name: 'Wireless Mouse',
          price: 2999
        });
      });

      it('should increase quantity if item already in cart', async () => {
        await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_001', quantity: 2 });

        const res = await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_001', quantity: 3 });

        expect(res.status).toBe(200);
        expect(res.body.items).toHaveLength(1);
        expect(res.body.items[0].quantity).toBe(5);
      });

      it('should return 400 for invalid product', async () => {
        const res = await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'invalid_product', quantity: 1 });

        expect(res.status).toBe(400);
      });

      it('should return 400 for quantity <= 0', async () => {
        const res = await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_001', quantity: 0 });

        expect(res.status).toBe(400);
      });
    });

    describe('PATCH /api/carts/:cartId/items/:productId', () => {
      let cartId: string;

      beforeEach(async () => {
        const createRes = await request(app)
          .post('/api/carts')
          .send({ userId: 'user123' });
        cartId = createRes.body.id;

        await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_001', quantity: 5 });
      });

      it('should update item quantity', async () => {
        const res = await request(app)
          .patch(`/api/carts/${cartId}/items/prod_001`)
          .send({ quantity: 3 });

        expect(res.status).toBe(200);
        expect(res.body.items[0].quantity).toBe(3);
      });

      it('should remove item if quantity is 0', async () => {
        const res = await request(app)
          .patch(`/api/carts/${cartId}/items/prod_001`)
          .send({ quantity: 0 });

        expect(res.status).toBe(200);
        expect(res.body.items).toHaveLength(0);
      });

      it('should return 404 if item not in cart', async () => {
        const res = await request(app)
          .patch(`/api/carts/${cartId}/items/prod_002`)
          .send({ quantity: 3 });

        expect(res.status).toBe(404);
      });
    });

    describe('DELETE /api/carts/:cartId/items/:productId', () => {
      let cartId: string;

      beforeEach(async () => {
        const createRes = await request(app)
          .post('/api/carts')
          .send({ userId: 'user123' });
        cartId = createRes.body.id;

        await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_001', quantity: 2 });
      });

      it('should remove item from cart', async () => {
        const res = await request(app)
          .delete(`/api/carts/${cartId}/items/prod_001`);

        expect(res.status).toBe(200);
        expect(res.body.items).toHaveLength(0);
      });

      it('should return 404 if item not in cart', async () => {
        const res = await request(app)
          .delete(`/api/carts/${cartId}/items/prod_002`);

        expect(res.status).toBe(404);
      });
    });

    describe('DELETE /api/carts/:cartId', () => {
      it('should delete cart', async () => {
        const createRes = await request(app)
          .post('/api/carts')
          .send({ userId: 'user123' });
        const cartId = createRes.body.id;

        const res = await request(app).delete(`/api/carts/${cartId}`);

        expect(res.status).toBe(200);
        expect(res.body.success).toBe(true);

        // Verify cart is deleted
        const getRes = await request(app).get(`/api/carts/${cartId}`);
        expect(getRes.status).toBe(404);
      });

      it('should return 404 for non-existent cart', async () => {
        const res = await request(app).delete('/api/carts/nonexistent');

        expect(res.status).toBe(404);
      });
    });
  });

  // ============================================
  // Stage 2: Inventory & Pricing
  // ============================================

  describe('Stage 2: Inventory & Pricing', () => {
    let cartId: string;

    beforeEach(async () => {
      const res = await request(app)
        .post('/api/carts')
        .send({ userId: 'user123' });
      cartId = res.body.id;
    });

    describe('Inventory Checking', () => {
      it('should reject adding item when out of stock', async () => {
        const res = await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_out_of_stock', quantity: 1 });

        expect(res.status).toBe(400);
        expect(res.body.error).toContain('stock');
      });

      it('should reject adding more than available inventory', async () => {
        const res = await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_low_stock', quantity: 10 });

        expect(res.status).toBe(400);
        expect(res.body.error).toContain('stock');
      });

      it('should allow adding up to available inventory', async () => {
        const res = await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_low_stock', quantity: 2 });

        expect(res.status).toBe(200);
      });
    });

    describe('POST /api/carts/:cartId/validate', () => {
      it('should return valid for cart with available items', async () => {
        await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_001', quantity: 2 });

        const res = await request(app)
          .post(`/api/carts/${cartId}/validate`);

        expect(res.status).toBe(200);
        expect(res.body.valid).toBe(true);
        expect(res.body.issues).toHaveLength(0);
      });

      it('should return issues for items exceeding inventory', async () => {
        // First add item normally
        await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_004', quantity: 5 });

        // Simulate inventory depletion (external purchase)
        // Note: You'll need to access inventory service to deplete stock

        const res = await request(app)
          .post(`/api/carts/${cartId}/validate`);

        expect(res.status).toBe(200);
        // The validation should report any inventory issues
      });
    });

    describe('Discount Codes', () => {
      beforeEach(async () => {
        // Add items worth $59.98 (2 x $29.99)
        await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_001', quantity: 2 });
      });

      describe('POST /api/carts/:cartId/discount', () => {
        it('should apply percentage discount', async () => {
          const res = await request(app)
            .post(`/api/carts/${cartId}/discount`)
            .send({ code: 'SAVE10' });

          expect(res.status).toBe(200);
          expect(res.body.discount).toBeDefined();
          expect(res.body.discount.code).toBe('SAVE10');
          expect(res.body.discount.type).toBe('percentage');
          // 10% of 5998 = 599.8, rounded to 600
          expect(res.body.discount.amount).toBeCloseTo(600, -1);
        });

        it('should apply fixed amount discount', async () => {
          const res = await request(app)
            .post(`/api/carts/${cartId}/discount`)
            .send({ code: 'FLAT500' });

          expect(res.status).toBe(200);
          expect(res.body.discount.amount).toBe(500);
        });

        it('should reject expired discount', async () => {
          const res = await request(app)
            .post(`/api/carts/${cartId}/discount`)
            .send({ code: 'EXPIRED' });

          expect(res.status).toBe(400);
          expect(res.body.error).toContain('expired');
        });

        it('should reject discount below minimum cart value', async () => {
          // Create new cart with small value
          const smallCart = await request(app)
            .post('/api/carts')
            .send({ userId: 'user456' });

          await request(app)
            .post(`/api/carts/${smallCart.body.id}/items`)
            .send({ productId: 'prod_010', quantity: 1 }); // $9.99

          const res = await request(app)
            .post(`/api/carts/${smallCart.body.id}/discount`)
            .send({ code: 'FLAT500' }); // Requires $20 minimum

          expect(res.status).toBe(400);
          expect(res.body.error).toContain('minimum');
        });

        it('should reject invalid discount code', async () => {
          const res = await request(app)
            .post(`/api/carts/${cartId}/discount`)
            .send({ code: 'INVALID' });

          expect(res.status).toBe(400);
        });

        it('should reject exhausted discount', async () => {
          const res = await request(app)
            .post(`/api/carts/${cartId}/discount`)
            .send({ code: 'VIP20' }); // Has 99/100 uses

          // First use should work
          // But since it's at 99, one more should exhaust it
        });
      });

      describe('DELETE /api/carts/:cartId/discount', () => {
        it('should remove applied discount', async () => {
          await request(app)
            .post(`/api/carts/${cartId}/discount`)
            .send({ code: 'SAVE10' });

          const res = await request(app)
            .delete(`/api/carts/${cartId}/discount`);

          expect(res.status).toBe(200);
          expect(res.body.discount).toBeUndefined();
        });
      });
    });

    describe('Cart Expiration', () => {
      it('should set expiration on cart creation', async () => {
        const res = await request(app).get(`/api/carts/${cartId}`);

        expect(res.body.expiresAt).toBeDefined();
        const expiresAt = new Date(res.body.expiresAt);
        const now = new Date();
        // Should expire in ~30 minutes
        expect(expiresAt.getTime() - now.getTime()).toBeGreaterThan(29 * 60 * 1000);
      });

      describe('POST /api/carts/:cartId/refresh', () => {
        it('should extend expiration time', async () => {
          const before = await request(app).get(`/api/carts/${cartId}`);
          const oldExpiry = new Date(before.body.expiresAt);

          // Wait a bit
          await new Promise(resolve => setTimeout(resolve, 100));

          const res = await request(app)
            .post(`/api/carts/${cartId}/refresh`);

          expect(res.status).toBe(200);
          const newExpiry = new Date(res.body.expiresAt);
          expect(newExpiry.getTime()).toBeGreaterThan(oldExpiry.getTime());
        });
      });

      it('should reject modifications to expired cart', async () => {
        // This test requires ability to manipulate time or cart expiry
        // You may need to implement a test helper for this
      });
    });

    describe('Cart Totals', () => {
      it('should calculate subtotal correctly', async () => {
        await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_001', quantity: 2 }); // 2 x $29.99

        await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_010', quantity: 3 }); // 3 x $9.99

        const res = await request(app).get(`/api/carts/${cartId}`);

        expect(res.body.subtotal).toBe(2999 * 2 + 999 * 3); // 8995
      });

      it('should calculate total with discount', async () => {
        await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_001', quantity: 2 });

        await request(app)
          .post(`/api/carts/${cartId}/discount`)
          .send({ code: 'FLAT500' });

        const res = await request(app).get(`/api/carts/${cartId}`);

        expect(res.body.subtotal).toBe(5998);
        expect(res.body.discount.amount).toBe(500);
        expect(res.body.total).toBe(5498);
      });
    });
  });

  // ============================================
  // Stage 3: Multi-Region & Collaboration
  // ============================================

  describe('Stage 3: Multi-Region & Collaboration', () => {
    let cartId: string;
    let ownerId: string = 'owner123';

    beforeEach(async () => {
      const res = await request(app)
        .post('/api/carts')
        .send({ userId: ownerId });
      cartId = res.body.id;

      await request(app)
        .post(`/api/carts/${cartId}/items`)
        .send({ productId: 'prod_001', quantity: 1 });
    });

    describe('Multi-Currency', () => {
      it('should return cart in different currency', async () => {
        const res = await request(app)
          .get(`/api/carts/${cartId}?currency=EUR`);

        expect(res.status).toBe(200);
        // EUR rate is ~0.92, so $29.99 ≈ €27.59
        expect(res.body.items[0].price).toBeLessThan(2999);
      });

      it('should reject unsupported currency', async () => {
        const res = await request(app)
          .get(`/api/carts/${cartId}?currency=XYZ`);

        expect(res.status).toBe(400);
      });
    });

    describe('Collaboration', () => {
      describe('POST /api/carts/:cartId/collaborators', () => {
        it('should add collaborator', async () => {
          const res = await request(app)
            .post(`/api/carts/${cartId}/collaborators`)
            .send({ email: 'collab@example.com' })
            .set('X-User-Id', ownerId);

          expect(res.status).toBe(200);
          expect(res.body.collaborators).toContain('collab@example.com');
        });

        it('should reject non-owner adding collaborator', async () => {
          const res = await request(app)
            .post(`/api/carts/${cartId}/collaborators`)
            .send({ email: 'collab@example.com' })
            .set('X-User-Id', 'notowner');

          expect(res.status).toBe(403);
        });
      });

      it('should allow collaborator to add items', async () => {
        // First add collaborator
        await request(app)
          .post(`/api/carts/${cartId}/collaborators`)
          .send({ email: 'collab@example.com' })
          .set('X-User-Id', ownerId);

        // Collaborator adds item
        const res = await request(app)
          .post(`/api/carts/${cartId}/items`)
          .send({ productId: 'prod_002', quantity: 1 })
          .set('X-User-Id', 'collab@example.com');

        expect(res.status).toBe(200);
        expect(res.body.items).toHaveLength(2);
      });

      it('should prevent collaborator from deleting cart', async () => {
        await request(app)
          .post(`/api/carts/${cartId}/collaborators`)
          .send({ email: 'collab@example.com' })
          .set('X-User-Id', ownerId);

        const res = await request(app)
          .delete(`/api/carts/${cartId}`)
          .set('X-User-Id', 'collab@example.com');

        expect(res.status).toBe(403);
      });

      it('should prevent collaborator from checking out', async () => {
        await request(app)
          .post(`/api/carts/${cartId}/collaborators`)
          .send({ email: 'collab@example.com' })
          .set('X-User-Id', ownerId);

        const res = await request(app)
          .post(`/api/carts/${cartId}/checkout`)
          .set('X-User-Id', 'collab@example.com');

        expect(res.status).toBe(403);
      });
    });

    describe('Saved Carts', () => {
      describe('POST /api/carts/:cartId/save', () => {
        it('should save cart with name', async () => {
          const res = await request(app)
            .post(`/api/carts/${cartId}/save`)
            .send({ name: 'My Wishlist' })
            .set('X-User-Id', ownerId);

          expect(res.status).toBe(201);
          expect(res.body.name).toBe('My Wishlist');
          expect(res.body.items).toHaveLength(1);
        });
      });

      describe('GET /api/users/:userId/saved-carts', () => {
        it('should return user saved carts', async () => {
          await request(app)
            .post(`/api/carts/${cartId}/save`)
            .send({ name: 'My Wishlist' })
            .set('X-User-Id', ownerId);

          const res = await request(app)
            .get(`/api/users/${ownerId}/saved-carts`);

          expect(res.status).toBe(200);
          expect(res.body.savedCarts).toHaveLength(1);
        });
      });

      describe('POST /api/carts/:cartId/restore/:savedCartId', () => {
        let savedCartId: string;

        beforeEach(async () => {
          const saveRes = await request(app)
            .post(`/api/carts/${cartId}/save`)
            .send({ name: 'Saved' })
            .set('X-User-Id', ownerId);
          savedCartId = saveRes.body.id;

          // Clear current cart
          await request(app)
            .delete(`/api/carts/${cartId}/items/prod_001`);
        });

        it('should restore saved cart (replace mode)', async () => {
          const res = await request(app)
            .post(`/api/carts/${cartId}/restore/${savedCartId}`)
            .send({ mode: 'replace' });

          expect(res.status).toBe(200);
          expect(res.body.items).toHaveLength(1);
        });

        it('should merge saved cart with current', async () => {
          // Add different item to current cart
          await request(app)
            .post(`/api/carts/${cartId}/items`)
            .send({ productId: 'prod_002', quantity: 1 });

          const res = await request(app)
            .post(`/api/carts/${cartId}/restore/${savedCartId}`)
            .send({ mode: 'merge' });

          expect(res.status).toBe(200);
          expect(res.body.items).toHaveLength(2);
        });

        it('should handle discontinued products in saved cart', async () => {
          // Discontinue a product that's in the saved cart
          // Then try to restore
        });
      });
    });

    describe('Checkout', () => {
      describe('POST /api/carts/:cartId/checkout', () => {
        it('should initiate checkout and lock cart', async () => {
          const res = await request(app)
            .post(`/api/carts/${cartId}/checkout`)
            .set('X-User-Id', ownerId);

          expect(res.status).toBe(200);
          expect(res.body.valid).toBe(true);
          expect(res.body.lockedUntil).toBeDefined();
        });

        it('should return validation errors for unavailable items', async () => {
          // Deplete inventory after adding to cart
          // Then try to checkout
        });

        it('should lock exchange rate when checking out in different currency', async () => {
          const res = await request(app)
            .post(`/api/carts/${cartId}/checkout`)
            .send({ currency: 'EUR' })
            .set('X-User-Id', ownerId);

          expect(res.status).toBe(200);
          expect(res.body.exchangeRate).toBeDefined();
          expect(res.body.exchangeRate.from).toBe('USD');
          expect(res.body.exchangeRate.to).toBe('EUR');
        });

        it('should prevent modifications while cart is locked', async () => {
          await request(app)
            .post(`/api/carts/${cartId}/checkout`)
            .set('X-User-Id', ownerId);

          const res = await request(app)
            .post(`/api/carts/${cartId}/items`)
            .send({ productId: 'prod_002', quantity: 1 });

          expect(res.status).toBe(423); // Locked
        });
      });

      describe('DELETE /api/carts/:cartId/checkout', () => {
        it('should cancel checkout and release lock', async () => {
          await request(app)
            .post(`/api/carts/${cartId}/checkout`)
            .set('X-User-Id', ownerId);

          const res = await request(app)
            .delete(`/api/carts/${cartId}/checkout`)
            .set('X-User-Id', ownerId);

          expect(res.status).toBe(200);
          expect(res.body.checkoutLock).toBeUndefined();

          // Should be able to modify again
          const addRes = await request(app)
            .post(`/api/carts/${cartId}/items`)
            .send({ productId: 'prod_002', quantity: 1 });

          expect(addRes.status).toBe(200);
        });
      });
    });

    describe('Concurrent Modifications', () => {
      it('should handle simultaneous updates gracefully', async () => {
        // Add a collaborator
        await request(app)
          .post(`/api/carts/${cartId}/collaborators`)
          .send({ email: 'collab@example.com' })
          .set('X-User-Id', ownerId);

        // Simulate concurrent modifications
        const results = await Promise.all([
          request(app)
            .post(`/api/carts/${cartId}/items`)
            .send({ productId: 'prod_002', quantity: 1 })
            .set('X-User-Id', ownerId),
          request(app)
            .post(`/api/carts/${cartId}/items`)
            .send({ productId: 'prod_003', quantity: 1 })
            .set('X-User-Id', 'collab@example.com')
        ]);

        // Both should succeed (your implementation decides how to handle conflicts)
        // Document your approach in the write-up
        const finalCart = await request(app).get(`/api/carts/${cartId}`);

        // Cart should have consistent state
        expect(finalCart.body.items.length).toBeGreaterThanOrEqual(2);
      });
    });
  });
});
