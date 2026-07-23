import { describe, expect, it } from "vitest";
import ExcelJS from "exceljs";
import { projectDataSchema } from "./project-schema";
import { buildProjectWorkbook } from "./export-excel";

const data = projectDataSchema.parse({ footprintLengthM: 12, footprintWidthM: 9 });

describe("Excel export", () => {
  it("produces a valid workbook with the four expected sheets", async () => {
    const buffer = await buildProjectWorkbook("Test Villa", data);
    const wb = new ExcelJS.Workbook();
    await wb.xlsx.load(buffer as ArrayBuffer);
    expect(wb.worksheets.map((w) => w.name)).toEqual([
      "Summary",
      "Materials",
      "Cost BOQ",
      "Labor Plan",
    ]);
  });

  it("writes the project name and headline totals into the summary", async () => {
    const buffer = await buildProjectWorkbook("Villa Kilifi", data);
    const wb = new ExcelJS.Workbook();
    await wb.xlsx.load(buffer as ArrayBuffer);
    const sum = wb.getWorksheet("Summary")!;
    const flat = JSON.stringify(sum.getSheetValues());
    expect(flat).toContain("Villa Kilifi");
    expect(flat).toContain("Cost — full contract (KES)");
  });

  it("BOQ sheet carries a grand total matching the cost engine", async () => {
    const buffer = await buildProjectWorkbook("Test", data);
    const wb = new ExcelJS.Workbook();
    await wb.xlsx.load(buffer as ArrayBuffer);
    const boq = wb.getWorksheet("Cost BOQ")!;
    let found = false;
    boq.eachRow((row) => {
      row.eachCell((cell) => {
        if (String(cell.value).includes("GRAND TOTAL (full contract)")) found = true;
      });
    });
    expect(found).toBe(true);
  });
});
