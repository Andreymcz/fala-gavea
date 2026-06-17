# QA Log 000077 | plan-000075 | 2026-06-17 21:43 UTC | wave-0-item-2-report-type-crud

source: plan-000075

## Brief

roadmap 1 item 2

## Q&A Log

**Q: What does "roadmap 1 item 2" mean in context?**

A: Item 2 of Wave 0 in roadmap-000071 (gavea-seguranca-demandas-app). Scope: ReportType CRUD --
4 endpoints (GET public, POST/PATCH/DELETE admin) + seed script + tests. The domain entity,
SQLAlchemy model, repository interface, and implementation were all created in plan-000073; this
plan adds the missing application and presentation layers.

**Q: What does the existing infrastructure cover?**

A: All of:
- `domain/entities/report_type.py` -- ReportType dataclass (id, name, description, active, created_at)
- `domain/repositories/report_type_repository.py` -- IReportTypeRepository (find_by_id, find_all_active, save)
- `infrastructure/repositories/sqlalchemy_report_type_repository.py` -- full implementation
- `infrastructure/database/models.py` -- ReportTypeModel with all columns
- `presentation/api/dependencies.py` -- get_report_type_repo already wired
- `domain/exceptions.py` -- ReportTypeNotFoundError and InvalidInputError already defined

**Q: Why does the seed script use stdlib urllib instead of httpx?**

A: To avoid adding a runtime dependency for a one-time operational script. The project's
runtime stack uses FastAPI (which ships httpx in the test extras via httpx), but a seed script
called by operators directly doesn't need the httpx package installed. Stdlib urllib is
sufficient for simple POST requests with JSON bodies and Bearer auth.

**Q: Why are there 10 test cases?**

A: Full CRUD coverage with auth boundary enforcement:
1-2: GET public behavior (empty + active-only filtering)
3-5: POST auth matrix (admin OK, citizen 403, unauthenticated 401)
6: POST validation (name too short)
7-8: PATCH happy path + 404
9-10: DELETE soft-delete behavior + 404

This covers all acceptance criteria from roadmap-000071 Item 2: "CRUD completo; DELETE nao
remove fisicamente; GET retorna apenas active=True."

**Q: Scope of plan-000075 vs. upcoming items?**

A: Plan-000075 is Wave 0 Item 2 only. Wave 1 (Items 3-4) adds Forwarding CRUD and the
frontend; Wave 2 (Items 5-7) adds ChromaDB and Ollama. No dependencies from 000075 block
Wave 2 (which only needs the Item 1 backend).
