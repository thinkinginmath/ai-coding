import { IPushService } from '../types';

/**
 * Mock Push Notification Service
 *
 * Simulates sending push notifications. In production, this would integrate
 * with Firebase Cloud Messaging, APNs, etc.
 *
 * DO NOT MODIFY - This simulates an external service
 */
export class MockPushService implements IPushService {
  private sentPushes: Array<{
    userId: string;
    title: string;
    body: string;
    data?: Record<string, unknown>;
    sentAt: Date;
    delivered: boolean;
  }> = [];

  // Simulate which users have push enabled (by userId pattern)
  // Users with IDs starting with 'push_' are considered to have push tokens
  private hasPushToken(userId: string): boolean {
    return userId.startsWith('push_') || Math.random() > 0.3;
  }

  // Simulate network latency
  private readonly latencyMs = 150;

  async send(
    userId: string,
    title: string,
    body: string,
    data?: Record<string, unknown>
  ): Promise<{ delivered: boolean }> {
    await this.simulateLatency();

    const delivered = this.hasPushToken(userId);

    this.sentPushes.push({
      userId,
      title,
      body,
      data,
      sentAt: new Date(),
      delivered
    });

    if (delivered) {
      console.log(`[MockPush] Delivered push to ${userId}: "${title}"`);
    } else {
      console.log(`[MockPush] No push token for ${userId}, notification not delivered`);
    }

    return { delivered };
  }

  // Test helper - get sent pushes
  getSentPushes() {
    return [...this.sentPushes];
  }

  // Test helper - clear sent pushes
  clearSentPushes() {
    this.sentPushes = [];
  }

  private simulateLatency(): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, this.latencyMs));
  }
}
