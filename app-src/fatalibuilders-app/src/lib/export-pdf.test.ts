import { describe, expect, it } from "vitest";
import { projectDataSchema } from "./project-schema";
import { buildProjectPdf } from "./export-pdf";

const data = projectDataSchema.parse({ footprintLengthM: 12, footprintWidthM: 9 });

describe("PDF export", () => {
  it("produces a non-trivial PDF buffer with a valid header", async () => {
    const pdf = await buildProjectPdf("Test Villa", data);
    expect(pdf.length).toBeGreaterThan(1000);
    // PDF files start with the "%PDF-" magic marker
    expect(pdf.subarray(0, 5).toString("latin1")).toBe("%PDF-");
    // and end with the EOF marker
    expect(pdf.subarray(-6).toString("latin1")).toContain("EOF");
  });

  it("handles a large multi-storey project without throwing", async () => {
    const big = projectDataSchema.parse({
      footprintLengthM: 40,
      footprintWidthM: 30,
      floors: 4,
      doorsCount: 60,
      windowsCount: 120,
    });
    const pdf = await buildProjectPdf("Big Block", big);
    expect(pdf.subarray(0, 5).toString("latin1")).toBe("%PDF-");
  });
});
