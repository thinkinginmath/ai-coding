import { IEmailService } from '../types';
import { v4 as uuidv4 } from 'uuid';

/**
 * Mock Email Service
 *
 * Simulates sending emails. In production, this would integrate with
 * SendGrid, SES, Mailgun, etc.
 *
 * DO NOT MODIFY - This simulates an external service
 */
export class MockEmailService implements IEmailService {
  private sentEmails: Array<{
    messageId: string;
    to: string;
    subject: string;
    body: string;
    sentAt: Date;
  }> = [];

  // Simulate network latency
  private readonly latencyMs = 100;

  // Simulate occasional failures (5% failure rate)
  private readonly failureRate = 0.05;

  async send(to: string, subject: string, body: string): Promise<{ messageId: string }> {
    await this.simulateLatency();

    if (Math.random() < this.failureRate) {
      throw new Error('Email service temporarily unavailable');
    }

    const messageId = uuidv4();

    this.sentEmails.push({
      messageId,
      to,
      subject,
      body,
      sentAt: new Date()
    });

    console.log(`[MockEmail] Sent email to ${to}: "${subject}"`);

    return { messageId };
  }

  // Test helper - get sent emails
  getSentEmails() {
    return [...this.sentEmails];
  }

  // Test helper - clear sent emails
  clearSentEmails() {
    this.sentEmails = [];
  }

  private simulateLatency(): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, this.latencyMs));
  }
}
