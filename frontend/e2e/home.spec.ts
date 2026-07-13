import { expect, test } from "@playwright/test"

test("home shows brand", async ({ page }) => {
  await page.goto("/")
  await expect(page.getByText("Tutoring Manager")).toBeVisible()
})
