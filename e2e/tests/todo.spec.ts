import { expect, test, type BrowserContext, type Page } from "@playwright/test";

const password = "Password123";

function uniqueEmail(label: string) {
  return `e2e-${label}-${Date.now()}@example.com`;
}

async function register(page: Page, email: string) {
  await page.goto("/register");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm Password").fill(password);
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page.getByText("My Todos", { exact: true })).toBeVisible();
}

async function logout(page: Page) {
  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("button", { name: "Sign In" })).toBeVisible();
}

test("register, create, complete, verify, and logout", async ({ page }) => {
  await register(page, uniqueEmail("journey"));

  await page.getByRole("button", { name: "Add Todo" }).click();
  await page.getByLabel("Title").fill("Finish Tier 2 E2E");
  await page.getByLabel("Description (optional)").fill("Created by Playwright");
  await page.getByRole("button", { name: "Create", exact: true }).click();

  const todo = page.getByText("Finish Tier 2 E2E", { exact: true });
  await expect(todo).toBeVisible();
  const checkbox = page.locator('[id^="todo-"]').first();
  await checkbox.click();
  await expect(todo).toHaveClass(/line-through/);

  await logout(page);
});

test("a second user cannot see a private todo", async ({ browser }) => {
  const userA: BrowserContext = await browser.newContext();
  const pageA = await userA.newPage();
  const privateTitle = `Private todo ${Date.now()}`;

  await register(pageA, uniqueEmail("owner"));
  await pageA.getByRole("button", { name: "Add Todo" }).click();
  await pageA.getByLabel("Title").fill(privateTitle);
  await pageA.getByRole("button", { name: "Create", exact: true }).click();
  await expect(pageA.getByText(privateTitle, { exact: true })).toBeVisible();

  const userB: BrowserContext = await browser.newContext();
  const pageB = await userB.newPage();
  await register(pageB, uniqueEmail("other"));
  await expect(pageB.getByText(privateTitle, { exact: true })).not.toBeVisible();

  await userA.close();
  await userB.close();
});
