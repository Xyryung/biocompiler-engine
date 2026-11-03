// Record the actual application; run the API and production dashboard first.
import { chromium } from "@playwright/test";
import { mkdir, writeFile, copyFile } from "node:fs/promises";
import { resolve } from "node:path";

const output = resolve(import.meta.dirname, "../../../artifacts/demo");
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  recordVideo: { dir: output, size: { width: 1920, height: 1080 } },
  reducedMotion: "reduce",
});
const page = await context.newPage();
const start = performance.now();
const waitUntil = async seconds => {
  const remaining = seconds * 1000 - (performance.now() - start);
  if (remaining > 0) await new Promise(resolve => setTimeout(resolve, remaining));
};
const errors = [];
page.on("pageerror", error => errors.push(error.message));
await page.goto("http://127.0.0.1:3000");
await waitUntil(15);
const goal = page.getByRole("textbox", { name: "Research goal" });
await goal.fill("");
await goal.pressSequentially("Design a PET-degrading enzyme assay stable at 45C.", { delay: 60 });
await waitUntil(30);
await page.getByRole("button", { name: "Compile experiment" }).click();
await page.getByText("Simulation passed", { exact: false }).waitFor({ timeout: 30000 });
await waitUntil(45);
await page.locator(".specpanel").scrollIntoViewIfNeeded();
await waitUntil(60);
await page.getByRole("button", { name: "JSON", exact: true }).click();
await waitUntil(70);
await page.getByRole("button", { name: "Overview", exact: true }).click();
await waitUntil(75);
await page.locator(".protocolcode").evaluate(el => { el.scrollTop = 140; });
await waitUntil(88);
await page.evaluate(()=>window.scrollTo({ top: 280, behavior: "smooth" }));
await page.getByRole("checkbox", { name: /Demonstrate recovery/ }).check();
await waitUntil(92);
await page.getByRole("button", { name: "Compile experiment" }).click();
await page.getByText("Simulation passed", { exact: false }).waitFor({ timeout: 40000 });
await waitUntil(103);
await page.locator(".simulationpanel").scrollIntoViewIfNeeded();
await waitUntil(116);
await page.locator(".visionpanel").scrollIntoViewIfNeeded();
await page.getByRole("combobox").selectOption("A3");
await waitUntil(128);
await page.getByRole("combobox").selectOption("A1");
await waitUntil(135);
await page.locator(".provenance").scrollIntoViewIfNeeded();
await waitUntil(147);
await page.getByRole("button", { name: "Test safety refusal" }).click();
await page.getByRole("button", { name: "Compile experiment" }).click();
await page.getByRole("heading", { name: "Stopped by the safety gate" }).waitFor();
await page.locator(".notice").scrollIntoViewIfNeeded();
await waitUntil(160);
await page.evaluate(()=>window.scrollTo({ top: 0, behavior: "smooth" }));
await waitUntil(165);
await page.screenshot({ path: resolve(output, "closing-frame.png") });
const video = page.video();
await context.close();
await copyFile(await video.path(), resolve(output, "demo-raw.webm"));
await browser.close();
if (errors.length) throw new Error(JSON.stringify(errors));
await writeFile(resolve(output, "recording.json"), JSON.stringify({
  recorded_at: new Date().toISOString(), timezone: "America/Panama", width: 1920, height: 1080,
  duration_target_seconds: 165, provider: "mock", simulation: "real local Opentrons 8.8.2",
  imagery: "synthetic", narration: "Windows system voice, synthesized",
  scenarios: ["successful compile", "injected failure and recovery", "safety refusal"],
}, null, 2));
console.log(`Recorded: ${resolve(output, "demo-raw.webm")}`);
