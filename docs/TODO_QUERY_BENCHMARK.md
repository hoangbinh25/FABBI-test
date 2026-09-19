# Todo query indexing benchmark

## Scope and method

This benchmark measures the three read paths served by `todo_service.get_todos`:

1. A user's newest todos page.
2. The count used for pagination.
3. A user's completed todos page.

The measurements used PostgreSQL 16 in Docker with a dedicated `tier3_benchmark`
database, seeded with 10,000 users and 1,000,000 todos. Seeding completed in
121.10 seconds. Both runs use the same user ID
`d943638b-44cc-434d-99e2-3a10fe365297`, `EXPLAIN (ANALYZE, BUFFERS)`, and a
limit of 20. Results are local benchmark evidence rather than a production SLA.

## Results

| Query | Before | After | Improvement | Plan change |
| --- | ---: | ---: | ---: | --- |
| User todos ordered by newest | 129.654 ms | 1.093 ms | 99.2% | Parallel sequential scan to `ix_todos_user_created_at_id` index scan |
| Count todos for a user | 58.993 ms | 1.083 ms | 98.2% | Parallel sequential scan to index-only scan |
| Completed todos ordered by newest | 236.901 ms | 0.679 ms | 99.7% | Parallel sequential scan to `ix_todos_user_completed_created_at_id` index scan |

The count plan performed 27 heap fetches after indexing. PostgreSQL can avoid
those fetches once vacuum has marked more index pages all-visible; this depends
on table churn and maintenance, so index-only scans should not be assumed to
be entirely heap-free in production.

## Queries

```sql
SELECT id, title, completed, created_at
FROM todos
WHERE user_id = :user_id
ORDER BY created_at DESC, id DESC
LIMIT 20;

SELECT count(*) FROM todos WHERE user_id = :user_id;

SELECT id, title, completed, created_at
FROM todos
WHERE user_id = :user_id AND completed = true
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

## Applied indexes

Migration `3c1f2e4d5a6b` creates these PostgreSQL B-tree indexes:

```sql
CREATE INDEX CONCURRENTLY ix_todos_user_created_at_id
  ON todos (user_id, created_at DESC, id DESC);

CREATE INDEX CONCURRENTLY ix_todos_user_completed_created_at_id
  ON todos (user_id, completed, created_at DESC, id DESC);
```

The first supports the standard per-user feed and its deterministic ordering.
The second makes the optional `completed` predicate selective while preserving
the same newest-first order. The service now explicitly orders pages by
`created_at DESC, id DESC`, so pagination has a stable order that matches the
index.

## Trade-offs and production rollout

- Every todo insert, delete, completion toggle, and `created_at` change must
  maintain these indexes. This adds write latency and index storage overhead;
  monitor write throughput, index size, and autovacuum after rollout.
- `CREATE INDEX CONCURRENTLY` avoids holding a table-wide write-blocking lock,
  but it takes longer, uses I/O, has multiple scan phases, and can wait for
  active transactions. Schedule it away from peak load and monitor progress
  through `pg_stat_progress_create_index`.
- The Alembic migration uses `autocommit_block()` because PostgreSQL forbids
  concurrent index creation inside a transaction. It is safe to retry only
  after inspecting for an invalid partial index. The downgrade also drops the
  indexes concurrently.
- Validate the plan on a production-like copy before release. Distribution,
  cache state, PostgreSQL version, and concurrent load can change the absolute
  timings; the baseline and post-index runs here were intentionally performed
  against the same dataset and query parameters.

## Reproduction

```bash
docker compose exec -T -e SEED_USERS=10000 -e SEED_TODOS=1000000 backend \
  python -m app.db.seed

docker compose exec -T postgres psql -U fabbi -d <benchmark_db> \
  -c "EXPLAIN (ANALYZE, BUFFERS) <query>"

docker compose exec -T backend alembic upgrade head
```
