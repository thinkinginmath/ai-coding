import { Router, Request, Response } from 'express';
import { INotificationService, IPreferencesService, CreateNotificationRequest } from '../types';

export function createNotificationRoutes(
  notificationService: INotificationService,
  preferencesService: IPreferencesService
): Router {
  const router = Router();

  // ============================================
  // TODO: Implement these route handlers
  // ============================================

  /**
   * POST /api/notifications
   * Create a new notification
   *
   * Request body: CreateNotificationRequest
   * Response: Notification
   */
  router.post('/notifications', async (req: Request, res: Response) => {
    // TODO: Implement
    // 1. Validate request body
    // 2. Call notificationService.create()
    // 3. Return created notification

    res.status(501).json({ error: 'Not implemented' });
  });

  /**
   * GET /api/users/:userId/notifications
   * Get notifications for a user
   *
   * Query params:
   *   - limit (default: 20, max: 100)
   *   - offset (default: 0)
   *   - unreadOnly (default: false)
   *
   * Response: PaginatedResponse<Notification>
   */
  router.get('/users/:userId/notifications', async (req: Request, res: Response) => {
    // TODO: Implement
    // 1. Parse pagination params from query
    // 2. Call notificationService.getByUserId()
    // 3. Return paginated response

    res.status(501).json({ error: 'Not implemented' });
  });

  /**
   * PATCH /api/notifications/:id/read
   * Mark a notification as read
   *
   * Request body: { userId: string }
   * Response: Notification
   */
  router.patch('/notifications/:id/read', async (req: Request, res: Response) => {
    // TODO: Implement
    // 1. Validate userId in body matches notification owner
    // 2. Call notificationService.markAsRead()
    // 3. Return updated notification

    res.status(501).json({ error: 'Not implemented' });
  });

  /**
   * POST /api/users/:userId/notifications/read-all
   * Mark all notifications as read for a user
   *
   * Response: { count: number }
   */
  router.post('/users/:userId/notifications/read-all', async (req: Request, res: Response) => {
    // TODO: Implement

    res.status(501).json({ error: 'Not implemented' });
  });

  /**
   * GET /api/users/:userId/preferences
   * Get notification preferences for a user
   *
   * Response: NotificationPreferences
   */
  router.get('/users/:userId/preferences', async (req: Request, res: Response) => {
    // TODO: Implement

    res.status(501).json({ error: 'Not implemented' });
  });

  /**
   * PUT /api/users/:userId/preferences
   * Update notification preferences for a user
   *
   * Request body: Partial<NotificationPreferences>
   * Response: NotificationPreferences
   */
  router.put('/users/:userId/preferences', async (req: Request, res: Response) => {
    // TODO: Implement

    res.status(501).json({ error: 'Not implemented' });
  });

  return router;
}
