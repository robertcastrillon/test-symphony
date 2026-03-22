# Execution Plan — ChronoTrack

## Detailed Analysis Summary

### Change Impact Assessment

| Area | Impact | Description |
|------|--------|-------------|
| User-facing changes | YES | Full React SPA with 9 pages, timer, charts |
| Structural changes | YES | New multi-service system from scratch |
| Data model changes | YES | 5 new tables: users, clients, projects, sessions, invoices |
| API changes | YES | 18+ new REST endpoints |
| NFR impact | YES | JWT auth, bcrypt, pagination, DB indexes, CI/CD |

### Risk Assessment

| Attribute | Value |
|-----------|-------|
| **Risk Level** | High |
| **Reason** | 9 units, cross-service dependencies, PDF generation, Telegram webhook, E2E tests |
| **Rollback Complexity** | Moderate (Git-based, all greenfield) |
| **Testing Complexity** | Complex (pytest async + Vitest + Playwright) |

---

## Workflow Visualization

```
INCEPTION PHASE
+-----------------------+-----------+
| Workspace Detection   | COMPLETED |
| Reverse Engineering   | SKIPPED   |
| Requirements Analysis | COMPLETED |
| User Stories          | SKIPPED   |
| Workflow Planning     | EXECUTE   |
| Application Design    | EXECUTE   |
| Units Generation      | EXECUTE   |
+-----------------------+-----------+

CONSTRUCTION PHASE (per unit x9)
+------------------------+-----------+
| Functional Design      | EXECUTE   |
| NFR Requirements       | EXECUTE   |
| NFR Design             | EXECUTE   |
| Infrastructure Design  | EXECUTE*  |
| Code Generation        | EXECUTE   |
+------------------------+-----------+
* Infrastructure Design only for Unit 1 (Docker, CI/CD)

+------------------------+-----------+
| Build and Test         | EXECUTE   |
+------------------------+-----------+

OPERATIONS PHASE
+------------+-------------+
| Operations | PLACEHOLDER |
+------------+-------------+
```

---

## Phases to Execute

### INCEPTION PHASE

- [x] Workspace Detection — COMPLETED
- [x] Reverse Engineering — SKIPPED (greenfield)
- [x] Requirements Analysis — COMPLETED
- [ ] User Stories — **SKIP**
  - **Rationale**: PRD contains comprehensive BDD acceptance criteria (Gherkin) for all features. User stories would be redundant.
- [x] Workflow Planning — IN PROGRESS
- [ ] Application Design — **EXECUTE**
  - **Rationale**: New system with 4 services, 5 data models, complex business rules (timer, invoicing, bot). Layered architecture needs explicit design.
- [ ] Units Generation — **EXECUTE**
  - **Rationale**: 9 units identified in PRD with cross-dependencies; formal generation ensures consistent structure and ordering.

### CONSTRUCTION PHASE (per unit)

For each of the 9 units:

- [ ] Functional Design — **EXECUTE**
  - **Rationale**: Each unit has new data models and business logic requiring detailed design.
- [ ] NFR Requirements — **EXECUTE**
  - **Rationale**: Security (JWT, bcrypt), performance (pagination, indexes), and observability apply throughout.
- [ ] NFR Design — **EXECUTE**
  - **Rationale**: NFR patterns (auth middleware, rate limiting, structured logging) must be incorporated.
- [ ] Infrastructure Design — **EXECUTE for Unit 1 only; SKIP for Units 2-9**
  - **Rationale**: Docker Compose + GitHub Actions defined once in Unit 1 (Foundation). Subsequent units extend existing infra.
- [ ] Code Generation — **EXECUTE** (always)
- [ ] Build and Test — **EXECUTE** (always, after all units)

### OPERATIONS PHASE

- [ ] Operations — PLACEHOLDER

---

## Unit Execution Order

```
Wave 1 (parallel):
  U1 — Foundation: Auth + DB + Docker        [backend, infra]
  U6 — React Frontend: Auth + Layout         [frontend, ui]

Wave 2 (after Wave 1):
  U2 — Client & Project Management API      [backend]
  (U3 starts after U2)

Wave 3 (after Wave 2):
  U3 — Time Tracking API                    [backend]

Wave 4 (parallel, after Wave 3):
  U4 — Invoice Generation                   [backend]
  U5 — Telegram Bot                         [backend, bot]
  U7 — Dashboard + Timer UI                 [frontend, ui]
  U8 — Projects + Clients + Sessions UI     [frontend, ui]

Wave 5 (after Wave 4):
  U9 — Reports + Invoices UI               [frontend, ui]
```

**Total units**: 9
**Total waves**: 5
**Max parallelism**: 4 agents simultaneous (Wave 4)

---

## Success Criteria

- **Primary Goal**: Fully functional ChronoTrack application running via Docker Compose
- **Key Deliverables**:
  - API with all 18+ endpoints passing tests (>= 80% coverage)
  - React SPA with 9 pages, timer, charts, PDF download
  - Telegram Bot (conditionally active)
  - GitHub Actions CI passing
  - Playwright E2E for UI tickets
- **Quality Gates**:
  - `docker-compose up` succeeds without errors
  - `GET /api/v1/health` returns 200
  - ruff + bandit clean
  - TypeScript strict mode passing
  - All security baseline rules (SECURITY-01 through SECURITY-15) verified
