import { expect, test } from "@playwright/test";

test("desktop and mobile command centre keeps evidence and controls truthful", async ({ page }) => {
  const consoleErrors: string[] = [];
  const externalRequests: string[] = [];
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => consoleErrors.push(error.message));
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (!/^(127\.0\.0\.1|localhost)$/.test(url.hostname)) externalRequests.push(request.url());
  });

  await page.setViewportSize({ width: 1440, height: 900 });
  const stateResponsePromise = page.waitForResponse((response) => response.url().endsWith("/api/v2/state"));
  await page.goto("/");
  await expect(page.getByTestId("watch-view")).toBeVisible();
  const stateResponse = await stateResponsePromise;
  const stateBytes = (await stateResponse.body()).byteLength;
  const stateMs = stateResponse.request().timing().responseEnd;
  const occupiedRows = await page.getByTestId("watch-row").count();
  const heapBytes = await page.evaluate(() => (performance as Performance & { memory?: { usedJSHeapSize: number } }).memory?.usedJSHeapSize ?? null);
  console.log(`Fixture load: ${occupiedRows} active rows; schema-v2 payload ${stateBytes} bytes / ${Math.round(stateMs)} ms; browser heap ${heapBytes ?? "unavailable"} bytes.`);
  await expect(page.getByRole("heading", { name: "Worker watch." })).toBeVisible();
  await page.screenshot({ path: "/tmp/snooze-watch-dark-desktop.png" });
  await expect(page.getByTestId("confirmed-effort").first()).toHaveText("Unknown");
  await expect(page.getByRole("button", { name: "Emergency stop" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Emergency stop" })).toHaveAttribute("title", /outside Snooze/i);

  await page.getByRole("button", { name: "Switch to light theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.screenshot({ path: "/tmp/snooze-watch-light-desktop.png" });

  await page.getByTestId("nav-queue").click();
  await expect(page.getByTestId("queue-view")).toBeVisible();
  await expect(page.getByTestId("queue-row")).toHaveCount(25);
  await expect(page.getByRole("button", { name: "Resume" }).first()).toBeDisabled();
  await page.screenshot({ path: "/tmp/snooze-queue-desktop.png" });
  await page.getByRole("button", { name: "Next page" }).click();
  await expect(page.getByTestId("queue-row").filter({ hasText: "task-025" })).toBeVisible();

  await page.getByTestId("nav-providers").click();
  await expect(page.getByTestId("providers-view")).toBeVisible();
  await page.screenshot({ path: "/tmp/snooze-providers-desktop.png" });

  const historyResponsePromise = page.waitForResponse((response) => response.url().endsWith("/api/state"));
  await page.getByTestId("nav-history").click();
  await expect(page.getByTestId("history-view")).toBeVisible();
  const historyResponse = await historyResponsePromise;
  const historyBytes = (await historyResponse.body()).byteLength;
  const historyMs = historyResponse.request().timing().responseEnd;
  await expect(page.getByTestId("history-row")).toHaveCount(25);
  console.log(`Fixture history: 10,002 available records; legacy snapshot ${historyBytes} bytes / ${Math.round(historyMs)} ms; rendered DOM rows ${await page.getByTestId("history-row").count()}.`);
  await page.screenshot({ path: "/tmp/snooze-history-desktop.png" });
  await page.getByRole("searchbox", { name: "Search history" }).fill("Completed assignment 000");
  await expect(page.getByText("Completed assignment 000")).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByTestId("nav-watch").click();
  await expect(page.getByTestId("watch-view")).toBeVisible();
  await page.screenshot({ path: "/tmp/snooze-watch-light-mobile.png" });
  await page.getByRole("button", { name: "Switch to dark theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.screenshot({ path: "/tmp/snooze-watch-dark-mobile.png" });
  const width = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(width).toBeLessThanOrEqual(390);
  await expect(page.locator(".mobile-worker-card").first()).toBeVisible();

  await page.getByTestId("nav-queue").click();
  await page.getByRole("button", { name: "Inspect Review release candidate" }).click();
  const drawer = page.getByRole("dialog", { name: "Task inspection drawer" });
  await expect(drawer).toBeVisible();
  await expect.poll(async () => page.locator(".kit-detail-drawer").evaluate((element) => element.getBoundingClientRect().left)).toBeLessThan(1);
  const drawerBounds = await page.locator(".kit-detail-drawer").evaluate((element) => {
    const bounds = element.getBoundingClientRect();
    return { left: bounds.left, width: bounds.width, viewport: innerWidth };
  });
  expect(drawerBounds.left).toBeLessThan(1);
  expect(drawerBounds.width).toBeGreaterThanOrEqual(390);
  await page.screenshot({ path: "/tmp/snooze-task-drawer-mobile.png" });
  await expect(drawer).toContainText('<img src=x onerror="alert(1)"> Keep this assigned prompt literal.');
  await expect(drawer.locator("img")).toHaveCount(0);
  await expect(drawer.locator('a[href^="javascript:"]')).toHaveCount(0);
  await expect(drawer.getByRole("link")).toHaveCount(1);
  await expect(drawer.getByRole("link")).toHaveAttribute("href", "https://docs.example.test/runbook");
  await page.keyboard.press("Tab");
  await expect(drawer.getByRole("button", { name: "Close task inspection" })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(drawer.getByRole("link")).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();

  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect.poll(() => page.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches)).toBe(true);
  await page.getByRole("button", { name: "Inspect Review release candidate" }).click();
  const reducedDrawer = page.locator(".kit-detail-drawer");
  const animationDuration = await reducedDrawer.evaluate((element) => Number.parseFloat(getComputedStyle(element).animationDuration));
  expect(animationDuration).toBeLessThan(0.001);
  await page.keyboard.press("Escape");
  expect(consoleErrors).toEqual([]);
  expect(externalRequests).toEqual([]);
});

test("settings persist through the real Snooze HTTP service", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await expect(page.getByTestId("watch-view")).toBeVisible();
  await page.getByTestId("nav-settings").click();
  await expect(page.getByTestId("settings-view")).toBeVisible();
  await page.screenshot({ path: "/tmp/snooze-settings-desktop.png" });
  const interval = page.getByLabel("Check interval");
  await interval.fill("600");
  await page.getByRole("button", { name: "Save interval" }).click();
  await expect(page.getByRole("status")).toContainText("saved by the local service");
  await page.reload();
  await expect(page.getByTestId("watch-view")).toBeVisible();
  await page.getByTestId("nav-settings").click();
  await expect(page.getByLabel("Check interval")).toHaveValue("600");
});

test("a failed refresh keeps the last received state visible", async ({ page }) => {
  let stateRequests = 0;
  await page.route("**/api/v2/state", async (route) => {
    stateRequests += 1;
    if (stateRequests === 1) return route.continue();
    return route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ error: "fixture refresh unavailable" }) });
  });
  await page.goto("/");
  await expect(page.getByTestId("watch-view")).toBeVisible();
  await page.getByRole("button", { name: "Check now" }).click();
  await expect(page.locator(".global-stale")).toContainText("fixture refresh unavailable");
  await expect(page.getByTestId("watch-row").first()).toBeVisible();
});
