import express from 'express';
import { createNotificationRoutes } from './routes/notifications';
import { NotificationService } from './services/notification.service';
import { PreferencesService } from './services/preferences.service';
import { RealTimeService } from './services/realtime.service';
import { MemoryStore } from './storage/memory.store';
import { MockEmailService } from './mocks/email.service';
import { MockPushService } from './mocks/push.service';

const app = express();
app.use(express.json());

// Initialize storage
const store = new MemoryStore();

// Initialize mock external services
const emailService = new MockEmailService();
const pushService = new MockPushService();

// Initialize core services
const preferencesService = new PreferencesService(store);
const realTimeService = new RealTimeService();
const notificationService = new NotificationService(
  store,
  preferencesService,
  realTimeService,
  emailService,
  pushService
);

// Mount routes
app.use('/api', createNotificationRoutes(notificationService, preferencesService));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

const PORT = process.env.PORT || 3000;

const server = app.listen(PORT, () => {
  console.log(`Notification service running on port ${PORT}`);
});

// Initialize WebSocket server for real-time (if you choose this approach)
realTimeService.attachToServer(server);

export { app, server };
