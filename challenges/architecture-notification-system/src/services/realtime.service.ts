import { Server } from 'http';
import { WebSocketServer, WebSocket } from 'ws';
import { IRealTimeService, Notification } from '../types';

/**
 * Real-Time Service
 *
 * TODO: Implement this service
 *
 * This service handles real-time delivery of notifications to connected users.
 *
 * The starter code sets up WebSocket infrastructure, but you can:
 * 1. Use this WebSocket approach
 * 2. Replace with Server-Sent Events (SSE)
 * 3. Implement long-polling
 * 4. Use a different approach entirely
 *
 * In your DESIGN.md, explain:
 * - Why you chose your real-time approach
 * - How it would scale to 500k users
 * - What happens when a user reconnects after being offline
 */
export class RealTimeService implements IRealTimeService {
  private wss: WebSocketServer | null = null;
  private connections: Map<string, WebSocket[]> = new Map();

  /**
   * Attach WebSocket server to HTTP server
   * Called from index.ts during startup
   */
  attachToServer(server: Server): void {
    this.wss = new WebSocketServer({ server, path: '/ws' });

    this.wss.on('connection', (ws: WebSocket, req) => {
      // TODO: Implement connection handling
      //
      // 1. Extract userId from query string or auth token
      // 2. Store connection in this.connections map
      // 3. Handle disconnect to clean up
      //
      // Example URL: ws://localhost:3000/ws?userId=user123

      const url = new URL(req.url || '', 'http://localhost');
      const userId = url.searchParams.get('userId');

      if (!userId) {
        ws.close(4001, 'userId required');
        return;
      }

      // Store connection
      const userConnections = this.connections.get(userId) || [];
      userConnections.push(ws);
      this.connections.set(userId, userConnections);

      console.log(`[RealTime] User ${userId} connected. Total connections: ${userConnections.length}`);

      ws.on('close', () => {
        const conns = this.connections.get(userId) || [];
        const index = conns.indexOf(ws);
        if (index > -1) {
          conns.splice(index, 1);
        }
        if (conns.length === 0) {
          this.connections.delete(userId);
        } else {
          this.connections.set(userId, conns);
        }
        console.log(`[RealTime] User ${userId} disconnected`);
      });

      // Send confirmation
      ws.send(JSON.stringify({ type: 'connected', userId }));
    });

    console.log('[RealTime] WebSocket server initialized');
  }

  async send(userId: string, notification: Notification): Promise<void> {
    // TODO: Implement
    //
    // Send notification to all connections for this user
    // Consider: What if user is not connected?

    throw new Error('Not implemented');
  }

  isConnected(userId: string): boolean {
    // TODO: Implement
    //
    // Return true if user has at least one active connection

    throw new Error('Not implemented');
  }
}
