import { IPreferencesService, NotificationPreferences } from '../types';
import { MemoryStore } from '../storage/memory.store';

/**
 * Default preferences for new users
 */
const DEFAULT_PREFERENCES: Omit<NotificationPreferences, 'userId'> = {
  channels: {
    mention: ['in_app', 'email', 'push'],
    task_assignment: ['in_app', 'email', 'push'],
    comment: ['in_app'],
    system_alert: ['in_app', 'email']
  },
  quietHours: {
    enabled: false,
    start: '22:00',
    end: '08:00',
    timezone: 'UTC'
  }
};

/**
 * Preferences Service
 *
 * TODO: Implement this service
 *
 * Handles user notification preferences including:
 * - Which channels to use for each notification type
 * - Quiet hours configuration
 */
export class PreferencesService implements IPreferencesService {
  constructor(private store: MemoryStore) {}

  async get(userId: string): Promise<NotificationPreferences> {
    // TODO: Implement
    //
    // Return stored preferences or default preferences for new users

    throw new Error('Not implemented');
  }

  async update(
    userId: string,
    preferences: Partial<NotificationPreferences>
  ): Promise<NotificationPreferences> {
    // TODO: Implement
    //
    // Merge provided preferences with existing (or default)
    // Save and return updated preferences

    throw new Error('Not implemented');
  }
}

export { DEFAULT_PREFERENCES };
