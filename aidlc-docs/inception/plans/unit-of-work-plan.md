# Unit of Work Plan — ChronoTrack

## Decision Notes

Units are fully defined in PRD Section 8 with clear boundaries, labels, priorities, and dependencies.
No clarifying questions needed — decomposition is unambiguous.

## Execution Checklist

- [x] Analyze PRD Section 8 + requirements + application design
- [x] Confirm 9 units with dependency ordering
- [x] Generate unit-of-work.md
- [x] Generate unit-of-work-dependency.md
- [x] Generate unit-of-work-story-map.md
- [x] Validate all units have complete definitions

## Units Summary

| Unit | Name | Wave | Labels | Depends On |
|------|------|------|--------|-----------|
| U1 | Foundation — Auth + DB + Docker | 1 | backend, infra | — |
| U2 | Client & Project Management API | 2 | backend | U1 |
| U3 | Time Tracking API | 3 | backend | U2 |
| U4 | Invoice Generation | 4 | backend | U3 |
| U5 | Telegram Bot | 4 | backend, bot | U3 |
| U6 | React Frontend — Auth + Layout | 1 | frontend, ui | — |
| U7 | Dashboard + Timer UI | 4 | frontend, ui | U3, U6 |
| U8 | Projects + Clients + Sessions UI | 4 | frontend, ui | U3, U6 |
| U9 | Reports + Invoices UI | 5 | frontend, ui | U4, U8 |
