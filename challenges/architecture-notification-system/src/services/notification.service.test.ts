/**
 * Test Suite for Notification Service
 *
 * These tests verify the basic functionality of your implementation.
 * You should add more tests as you implement features.
 */

import { NotificationService } from './notification.service';
import { PreferencesService } from './preferences.service';
import { RealTimeService } from './realtime.service';
import { MemoryStore } from '../storage/memory.store';
import { MockEmailService } from '../mocks/email.service';
import { MockPushService } from '../mocks/push.service';
import { CreateNotificationRequest } from '../types';

describe('NotificationService', () => {
  let service: NotificationService;
  let store: MemoryStore;
  let emailService: MockEmailService;
  let pushService: MockPushService;

  beforeEach(() => {
    store = new MemoryStore();
    emailService = new MockEmailService();
    pushService = new MockPushService();

    const preferencesService = new PreferencesService(store);
    const realTimeService = new RealTimeService();

    service = new NotificationService(
      store,
      preferencesService,
      realTimeService,
      emailService,
      pushService
    );
  });

  describe('create', () => {
    const validRequest: CreateNotificationRequest = {
      userId: 'user123',
      tenantId: 'tenant456',
      type: 'mention',
      title: 'You were mentioned',
      body: 'John mentioned you in a comment'
    };

    it('should create a notification with all required fields', async () => {
      const notification = await service.create(validRequest);

      expect(notification).toMatchObject({
        userId: 'user123',
        tenantId: 'tenant456',
        type: 'mention',
        title: 'You were mentioned',
        body: 'John mentioned you in a comment',
        read: false
      });
      expect(notification.id).toBeDefined();
      expect(notification.createdAt).toBeInstanceOf(Date);
    });

    it('should store the notification', async () => {
      const notification = await service.create(validRequest);

      const result = await service.getByUserId('user123', { limit: 10, offset: 0 });
      expect(result.data).toHaveLength(1);
      expect(result.data[0].id).toBe(notification.id);
    });

    // TODO: Add more tests for:
    // - Delivery via email when preferences indicate
    // - Delivery via push when preferences indicate
    // - Respecting quiet hours
    // - Handling delivery failures
  });

  describe('getByUserId', () => {
    beforeEach(async () => {
      // Create some test notifications
      for (let i = 0; i < 25; i++) {
        await service.create({
          userId: 'user123',
          tenantId: 'tenant456',
          type: 'comment',
          title: `Notification ${i}`,
          body: `Body ${i}`
        });
      }
    });

    it('should return paginated results', async () => {
      const result = await service.getByUserId('user123', { limit: 10, offset: 0 });

      expect(result.data).toHaveLength(10);
      expect(result.pagination.total).toBe(25);
      expect(result.pagination.hasMore).toBe(true);
    });

    it('should respect offset parameter', async () => {
      const result = await service.getByUserId('user123', { limit: 10, offset: 20 });

      expect(result.data).toHaveLength(5);
      expect(result.pagination.hasMore).toBe(false);
    });

    it('should filter by unread only', async () => {
      // Mark some as read first (implement markAsRead first)
      // Then test filtering

      const result = await service.getByUserId(
        'user123',
        { limit: 10, offset: 0 },
        { unreadOnly: true }
      );

      expect(result.data.every(n => !n.read)).toBe(true);
    });
  });

  describe('markAsRead', () => {
    it('should mark notification as read', async () => {
      const notification = await service.create({
        userId: 'user123',
        tenantId: 'tenant456',
        type: 'mention',
        title: 'Test',
        body: 'Test body'
      });

      const updated = await service.markAsRead(notification.id, 'user123');

      expect(updated?.read).toBe(true);
      expect(updated?.readAt).toBeInstanceOf(Date);
    });

    it('should return null for non-existent notification', async () => {
      const result = await service.markAsRead('nonexistent', 'user123');

      expect(result).toBeNull();
    });

    it('should not allow marking another user\'s notification', async () => {
      const notification = await service.create({
        userId: 'user123',
        tenantId: 'tenant456',
        type: 'mention',
        title: 'Test',
        body: 'Test body'
      });

      const result = await service.markAsRead(notification.id, 'differentUser');

      expect(result).toBeNull();
    });
  });

  describe('markAllAsRead', () => {
    it('should mark all notifications as read and return count', async () => {
      // Create 5 notifications
      for (let i = 0; i < 5; i++) {
        await service.create({
          userId: 'user123',
          tenantId: 'tenant456',
          type: 'comment',
          title: `Notification ${i}`,
          body: `Body ${i}`
        });
      }

      const count = await service.markAllAsRead('user123');

      expect(count).toBe(5);

      const result = await service.getByUserId(
        'user123',
        { limit: 10, offset: 0 },
        { unreadOnly: true }
      );
      expect(result.data).toHaveLength(0);
    });
  });
});
