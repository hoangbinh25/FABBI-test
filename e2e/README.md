# Playwright E2E tests

Start the application first from the repository root:

```bash
docker compose up --build
```

In another terminal, install E2E dependencies and Chromium once:

```bash
cd e2e
npm install
npx playwright install chromium
```

Run the suite headlessly:

```bash
npx playwright test
```

Run with a visible browser:

```bash
npx playwright test --headed
```

The tests use `http://127.0.0.1:3000` by default. Point to another deployed environment with `E2E_BASE_URL`, for example:

```bash
E2E_BASE_URL=http://localhost:3000 npx playwright test
```
