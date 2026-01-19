import { v4 as uuidv4 } from 'uuid';
import {
  INotificationService,
  IPreferencesService,
  IRealTimeService,
  IEmailService,
  IPushService,
  Notification,
  CreateNotificationRequest,
  PaginationParams,
  PaginatedResponse
} from '../types';
import { MemoryStore } from '../storage/memory.store';

/**
 * Notification Service
 *
 * TODO: Implement this service
 *
 * This is the core service that handles:
 * 1. Creating notifications
 * 2. Delivering notifications via appropriate channels (based on preferences)
 * 3. Retrieving notifications for users
 * 4. Marking notifications as read
 *
 * Consider:
 * - What happens if email/push delivery fails?
 * - Should delivery be synchronous or asynchronous?
 * - How do you handle quiet hours?
 * - What if a user has no preferences set?
 */
export class NotificationService implements INotificationService {
  constructor(
    private store: MemoryStore,
    private preferencesService: IPreferencesService,
    private realTimeService: IRealTimeService,
    private emailService: IEmailService,
    private pushService: IPushService
  ) {}

  async create(request: CreateNotificationRequest): Promise<Notification> {
    // TODO: Implement
    //
    // Steps to consider:
    // 1. Create the notification object
    // 2. Save to storage
    // 3. Get user preferences
    // 4. Deliver via appropriate channels (in_app, email, push)
    // 5. Handle delivery failures gracefully
    //
    // Questions for your design doc:
    // - Should delivery block the response or happen async?
    // - What's the retry strategy for failed deliveries?
    // - How do you ensure exactly-once delivery?

    throw new Error('Not implemented');
  }

  async getByUserId(
    userId: string,
    pagination: PaginationParams,
    filter?: { unreadOnly?: boolean }
  ): Promise<PaginatedResponse<Notification>> {
    // TODO: Implement
    //
    // Use the store methods to retrieve notifications
    // Apply pagination and filters

    throw new Error('Not implemented');
  }

  async markAsRead(notificationId: string, userId: string): Promise<Notification | null> {
    // TODO: Implement
    //
    // 1. Get notification from store
    // 2. Verify it belongs to the user
    // 3. Update read status
    // 4. Save back to store

    throw new Error('Not implemented');
  }

  async markAllAsRead(userId: string): Promise<number> {
    // TODO: Implement
    //
    // Mark all unread notifications for user as read
    // Return count of notifications marked

    throw new Error('Not implemented');
  }
}
