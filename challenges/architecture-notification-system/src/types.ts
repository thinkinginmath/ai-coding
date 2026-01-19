// ============================================
// Core Types - DO NOT MODIFY
// ============================================

export type NotificationType = 'mention' | 'task_assignment' | 'comment' | 'system_alert';

export type DeliveryChannel = 'in_app' | 'email' | 'push';

export interface Notification {
  id: string;
  userId: string;
  tenantId: string;
  type: NotificationType;
  title: string;
  body: string;
  data?: Record<string, unknown>;  // Additional payload (e.g., link to task)
  read: boolean;
  createdAt: Date;
  readAt?: Date;
}

export interface CreateNotificationRequest {
  userId: string;
  tenantId: string;
  type: NotificationType;
  title: string;
  body: string;
  data?: Record<string, unknown>;
}

export interface NotificationPreferences {
  userId: string;
  channels: {
    mention: DeliveryChannel[];
    task_assignment: DeliveryChannel[];
    comment: DeliveryChannel[];
    system_alert: DeliveryChannel[];
  };
  quietHours?: {
    enabled: boolean;
    start: string;  // HH:mm format
    end: string;    // HH:mm format
    timezone: string;
  };
}

export interface PaginationParams {
  limit: number;
  offset: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
}

// ============================================
// Service Interfaces - Implement these
// ============================================

export interface INotificationService {
  /**
   * Create and deliver a notification
   * Should check user preferences and deliver via appropriate channels
   */
  create(request: CreateNotificationRequest): Promise<Notification>;

  /**
   * Get notifications for a user with pagination
   * Should support filtering by read/unread status
   */
  getByUserId(
    userId: string,
    pagination: PaginationParams,
    filter?: { unreadOnly?: boolean }
  ): Promise<PaginatedResponse<Notification>>;

  /**
   * Mark a notification as read
   */
  markAsRead(notificationId: string, userId: string): Promise<Notification | null>;

  /**
   * Mark all notifications as read for a user
   */
  markAllAsRead(userId: string): Promise<number>;
}

export interface IPreferencesService {
  /**
   * Get user's notification preferences
   * Should return default preferences if none set
   */
  get(userId: string): Promise<NotificationPreferences>;

  /**
   * Update user's notification preferences
   */
  update(userId: string, preferences: Partial<NotificationPreferences>): Promise<NotificationPreferences>;
}

export interface IRealTimeService {
  /**
   * Send a real-time notification to a user
   * Implementation details are up to you (WebSocket, SSE, polling, etc.)
   */
  send(userId: string, notification: Notification): Promise<void>;

  /**
   * Check if a user is currently connected
   */
  isConnected(userId: string): boolean;
}

// ============================================
// External Service Interfaces (Mocked)
// ============================================

export interface IEmailService {
  send(to: string, subject: string, body: string): Promise<{ messageId: string }>;
}

export interface IPushService {
  send(userId: string, title: string, body: string, data?: Record<string, unknown>): Promise<{ delivered: boolean }>;
}
