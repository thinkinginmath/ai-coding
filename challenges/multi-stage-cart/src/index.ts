import express from 'express';
import { createCartRoutes } from './routes/cart.routes';
import { CartService } from './services/cart.service';
import { MemoryStore } from './storage/memory.store';
import { MockInventoryService } from './mocks/inventory.service';
import { MockExchangeRateService } from './mocks/exchange-rate.service';
import { MockProductService } from './mocks/product.service';

const app = express();
app.use(express.json());

// Initialize storage
const store = new MemoryStore();

// Initialize mock services
const inventoryService = new MockInventoryService();
const exchangeRateService = new MockExchangeRateService();
const productService = new MockProductService();

// Initialize cart service
const cartService = new CartService(
  store,
  productService,
  inventoryService,
  exchangeRateService
);

// Mount routes
app.use('/api', createCartRoutes(cartService));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Error handler
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

const PORT = process.env.PORT || 3001;

const server = app.listen(PORT, () => {
  console.log(`Cart service running on port ${PORT}`);
});

export { app, server, store };
