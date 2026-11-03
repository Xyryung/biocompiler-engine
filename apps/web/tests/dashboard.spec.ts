import { test, expect } from "@playwright/test";

test("one request populates all five panes from the real backend", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", e=>errors.push(e.message));
  await page.goto("/");
  await expect(page.getByText("No robot connected. Plate imagery is synthetic.")).toBeVisible();
  await page.getByRole("button", { name: "Compile experiment" }).click();
  await expect(page.getByText("Simulation passed", { exact: false })).toBeVisible({ timeout: 30_000 });
  for (const title of ["Research goal", "Experiment specification", "Generated protocol", "Simulation evidence", "Plate observations"]) {
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
  }
  await expect(page.getByAltText(/96-well plate segmentation/)).toBeVisible();
  await expect(page.getByText("OFFLINE MOCK", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "JSON", exact: true }).click();
  await expect(page.locator(".specjson")).toContainText('"experiment_name"');
  await page.getByRole("combobox").selectOption("A1");
  await expect(page.getByRole("combobox")).toHaveValue("A1");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download .py" }).click();
  expect((await download).suggestedFilename()).toBe("pet-assay.py");
  await page.screenshot({ path: "../../artifacts/dashboard-1080p.png", fullPage: true });
  expect(errors).toEqual([]);
});

test("self-healing shows failed diagnostic and successful retry", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("checkbox", { name: /Demonstrate recovery/ }).check();
  await page.getByRole("button", { name: "Compile experiment" }).click();
  await expect(page.getByText("Simulation passed", { exact: false })).toBeVisible({ timeout: 40_000 });
  await expect(page.getByText("Failed — diagnostic sent for repair")).toBeVisible();
  await expect(page.locator(".attempts")).toContainText("INVALID_WELL");
  await expect(page.locator(".attempts")).toContainText("Attempt 2");
});

test("refusal is a deliberate state and clears old results", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Test safety refusal" }).click();
  await page.getByRole("button", { name: "Compile experiment" }).click();
  await expect(page.locator("section[role=alert]")).toContainText("Stopped by the safety gate");
  await expect(page.getByText("No protocol was compiled or simulated.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Generated protocol" })).toHaveCount(0);
});

test("network error is readable and retry remains possible", async ({ page }) => {
  await page.route("**/api/compile", route=>route.abort());
  await page.goto("/");
  await page.getByRole("button", { name: "Compile experiment" }).click();
  await expect(page.locator("section[role=alert]")).toContainText("Connection interrupted");
  await expect(page.getByRole("button", { name: "Compile experiment" })).toBeEnabled();
});

test("mobile layout remains usable and blank goals cannot run", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("textbox", { name: "Research goal" }).fill("     ");
  await expect(page.getByRole("button", { name: "Compile experiment" })).toBeDisabled();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});
