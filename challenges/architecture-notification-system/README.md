# Problem 1: Real-Time Notification System

## Background

You're building a notification system for a B2B SaaS platform with the following characteristics:
- 10,000 active companies (tenants)
- 500,000 total users
- Notifications include: mentions, task assignments, comments, system alerts
- Users access via web app and mobile app

## Requirements

1. Users receive notifications in near real-time (< 3 seconds)
2. Notifications persist and can be viewed later (read/unread status)
3. Users can configure notification preferences (email, push, in-app)
4. System must handle 100,000 notifications/hour at peak

## Your Task

### Part A: Design Document (40% of grade)

Create `DESIGN.md` with:
1. Your chosen architecture approach
2. At least 2 alternative approaches you considered
3. Trade-offs for each approach (pros/cons)
4. Why you chose your approach given the requirements
5. What would change if scale increased 100x

### Part B: Implementation (40% of grade)

Implement the core notification service:
- `POST /notifications` - Create a notification
- `GET /users/:userId/notifications` - Fetch user's notifications (with pagination)
- `PATCH /notifications/:id/read` - Mark notification as read
- `GET /users/:userId/preferences` - Get notification preferences
- `PUT /users/:userId/preferences` - Update notification preferences
- Real-time delivery mechanism of your choice

### Part C: Documentation (20% of grade)

Add to your `DESIGN.md`:
- How would you test this system?
- What are the failure modes and how would you handle them?
- What metrics would you monitor in production?

## Getting Started

```bash
npm install
npm run dev     # Start development server
npm test        # Run tests
```

## Project Structure

```
src/
├── index.ts              # Application entry point
├── types.ts              # TypeScript interfaces
├── routes/
│   └── notifications.ts  # API route handlers (implement here)
├── services/
│   ├── notification.service.ts  # Core logic (implement here)
│   └── realtime.service.ts      # Real-time delivery (implement here)
├── storage/
│   └── memory.store.ts   # In-memory storage (can replace)
└── mocks/
    ├── email.service.ts  # Mock email service
    └── push.service.ts   # Mock push notification service
```

## Grading Rubric

| Grade | Criteria |
|-------|----------|
| A | Thorough trade-off analysis, acknowledges complexity honestly, implementation matches stated design, identifies non-obvious failure modes |
| B | Reasonable architecture choice with some justification, working implementation, basic failure handling |
| C | Working implementation but weak reasoning, missed major trade-offs, design and implementation don't align |
| D | Implementation works but no meaningful architecture discussion |
