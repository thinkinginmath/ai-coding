import { Notification, NotificationPreferences } from '../types';

/**
 * In-memory storage implementation
 *
 * NOTE: This is provided for quick prototyping. You may:
 * 1. Use this as-is for the challenge
 * 2. Replace with a different storage solution if your design requires it
 * 3. Extend this class with additional methods
 *
 * In your DESIGN.md, discuss what storage you would use in production
 * and why.
 */
export class MemoryStore {
  private notifications: Map<string, Notification> = new Map();
  private preferences: Map<string, NotificationPreferences> = new Map();
  private userNotifications: Map<string, string[]> = new Map(); // userId -> notificationIds

  // ============================================
  // Notification Storage
  // ============================================

  saveNotification(notification: Notification): void {
    this.notifications.set(notification.id, notification);

    // Index by user
    const userNotifs = this.userNotifications.get(notification.userId) || [];
    userNotifs.unshift(notification.id); // Most recent first
    this.userNotifications.set(notification.userId, userNotifs);
  }

  getNotification(id: string): Notification | undefined {
    return this.notifications.get(id);
  }

  updateNotification(notification: Notification): void {
    this.notifications.set(notification.id, notification);
  }

  getNotificationsByUserId(
    userId: string,
    limit: number,
    offset: number
  ): { notifications: Notification[]; total: number } {
    const notificationIds = this.userNotifications.get(userId) || [];
    const total = notificationIds.length;

    const paginatedIds = notificationIds.slice(offset, offset + limit);
    const notifications = paginatedIds
      .map(id => this.notifications.get(id))
      .filter((n): n is Notification => n !== undefined);

    return { notifications, total };
  }

  getUnreadNotificationsByUserId(
    userId: string,
    limit: number,
    offset: number
  ): { notifications: Notification[]; total: number } {
    const notificationIds = this.userNotifications.get(userId) || [];
    const unreadIds = notificationIds.filter(id => {
      const notif = this.notifications.get(id);
      return notif && !notif.read;
    });

    const total = unreadIds.length;
    const paginatedIds = unreadIds.slice(offset, offset + limit);
    const notifications = paginatedIds
      .map(id => this.notifications.get(id))
      .filter((n): n is Notification => n !== undefined);

    return { notifications, total };
  }

  // ============================================
  // Preferences Storage
  // ============================================

  savePreferences(preferences: NotificationPreferences): void {
    this.preferences.set(preferences.userId, preferences);
  }

  getPreferences(userId: string): NotificationPreferences | undefined {
    return this.preferences.get(userId);
  }

  // ============================================
  // Utility Methods
  // ============================================

  clear(): void {
    this.notifications.clear();
    this.preferences.clear();
    this.userNotifications.clear();
  }

  getStats(): { notificationCount: number; userCount: number } {
    return {
      notificationCount: this.notifications.size,
      userCount: this.userNotifications.size
    };
  }
}
