import PDFDocument from "pdfkit";
import type { ProjectData } from "./project-schema";
import { CODE_PROFILES } from "@/engines/profiles";
import { computeMaterials } from "@/engines/materials/residential";
import { computeCost, formatKES } from "@/engines/cost";
import { computeLabor } from "@/engines/labor";

const NAVY = "#1e3a5f";
const GREY = "#6b7280";
const LIGHT = "#e8eef5";

/** Renders a project's estimate as an A4 PDF (BOQ + summaries). Resolves to a Buffer. */
export function buildProjectPdf(projectName: string, data: ProjectData): Promise<Buffer> {
  const materials = computeMaterials(data);
  const cost = computeCost(data);
  const labor = computeLabor(data);
  const profile = CODE_PROFILES[data.codeProfile].label;

  const doc = new PDFDocument({ size: "A4", margin: 40, bufferPages: true });
  const chunks: Buffer[] = [];
  doc.on("data", (c) => chunks.push(c as Buffer));

  const done = new Promise<Buffer>((resolve) => {
    doc.on("end", () => resolve(Buffer.concat(chunks)));
  });

  const pageWidth = doc.page.width - 80; // usable width
  const left = 40;

  // ---- Header ----
  doc.rect(0, 0, doc.page.width, 70).fill(NAVY);
  doc.fillColor("white").fontSize(18).font("Helvetica-Bold").text("FATALIBUILDERS", left, 20);
  doc.fontSize(9).font("Helvetica").text("CONSTRUCTION APP  ·  Project Estimate", left, 44);
  doc.fillColor("black");
  doc.moveDown(3);

  let y = 90;
  doc.fontSize(14).font("Helvetica-Bold").text(projectName, left, y);
  y += 20;
  doc
    .fontSize(9)
    .font("Helvetica")
    .fillColor(GREY)
    .text(
      `${data.country}  ·  ${data.floors} floor(s)  ·  ${data.footprintLengthM} × ${data.footprintWidthM} m  ·  ${profile}`,
      left,
      y,
    );
  doc.fillColor("black");
  y += 26;

  // ---- Cost BOQ table ----
  const cols = { item: left, qty: 320, unit: 365, rate: 405, amount: 475 };
  const drawRowHeader = (title: string) => {
    if (y > 720) {
      doc.addPage();
      y = 50;
    }
    doc.rect(left, y, pageWidth, 16).fill(NAVY);
    doc.fillColor("white").fontSize(9).font("Helvetica-Bold").text(title, left + 4, y + 4);
    doc.fillColor("black");
    y += 18;
    doc.fontSize(7.5).font("Helvetica-Bold").fillColor(GREY);
    doc.text("Item", cols.item + 4, y);
    doc.text("Qty", cols.qty, y, { width: 40, align: "right" });
    doc.text("Unit", cols.unit, y);
    doc.text("Rate", cols.rate, y, { width: 55, align: "right" });
    doc.text("Amount", cols.amount, y, { width: 70, align: "right" });
    doc.fillColor("black");
    y += 12;
  };

  doc.fontSize(12).font("Helvetica-Bold").text("Bill of Quantities (KES)", left, y);
  y += 18;

  for (const section of cost.sections) {
    drawRowHeader(section.title);
    doc.fontSize(8).font("Helvetica");
    for (const it of section.items) {
      if (y > 780) {
        doc.addPage();
        y = 50;
        drawRowHeader(section.title + " (cont.)");
        doc.fontSize(8).font("Helvetica");
      }
      doc.text(it.label, cols.item + 4, y, { width: 270 });
      doc.text(String(it.quantity), cols.qty, y, { width: 40, align: "right" });
      doc.text(it.unit, cols.unit, y);
      doc.text(it.rateFull.toLocaleString("en-KE"), cols.rate, y, { width: 55, align: "right" });
      doc.text(it.amountFull.toLocaleString("en-KE"), cols.amount, y, {
        width: 70,
        align: "right",
      });
      y += 13;
    }
    doc.font("Helvetica-Bold");
    doc.text("Subtotal", cols.rate - 40, y, { width: 95, align: "right" });
    doc.text(section.subtotalFull.toLocaleString("en-KE"), cols.amount, y, {
      width: 70,
      align: "right",
    });
    y += 18;
  }

  // ---- Totals block ----
  if (y > 700) {
    doc.addPage();
    y = 50;
  }
  doc.rect(left, y, pageWidth, 68).fill(LIGHT);
  doc.fillColor("black").fontSize(9).font("Helvetica");
  const totalLine = (label: string, value: number, bold = false) => {
    doc.font(bold ? "Helvetica-Bold" : "Helvetica").fontSize(bold ? 11 : 9);
    doc.text(label, left + 10, y + 6, { width: 300 });
    doc.text(formatKES(value), left + 10, y + 6, { width: pageWidth - 20, align: "right" });
    y += bold ? 18 : 15;
  };
  totalLine("Measured works", cost.measuredWorksFull);
  totalLine("Contingency (5%)", cost.contingencyFull);
  totalLine("GRAND TOTAL — full contract", cost.grandTotalFull, true);
  totalLine("Labour only (client supplies materials)", cost.grandTotalLabour);
  y += 14;

  // ---- Key quantities & schedule ----
  if (y > 680) {
    doc.addPage();
    y = 50;
  }
  doc.fontSize(11).font("Helvetica-Bold").fillColor("black").text("Key materials", left, y);
  y += 16;
  doc.fontSize(9).font("Helvetica");
  const t = materials.totals;
  const mats = [
    `Cement: ${t.cementBags} bags`,
    `Sand: ${t.sandM3} m³`,
    `Ballast: ${t.ballastM3} m³`,
    `Blocks: ${t.blocks}`,
    `Steel: ${t.steelKg} kg`,
    ...(t.roofCoverM2 > 0 ? [`Roof cover: ${t.roofCoverM2} m²`] : []),
    ...(t.paintLitres > 0 ? [`Paint: ${t.paintLitres} L`] : []),
  ];
  doc.text(mats.join("    ·    "), left, y, { width: pageWidth });
  y += 26;
  doc.fontSize(11).font("Helvetica-Bold").text("Schedule", left, y);
  y += 16;
  doc
    .fontSize(9)
    .font("Helvetica")
    .text(
      `Estimated duration ≈ ${labor.calendarWeeks} weeks  ·  peak crew ${labor.peakCrew}  ·  labour cost ${formatKES(labor.totalLaborCostKES)}`,
      left,
      y,
      { width: pageWidth },
    );

  // ---- Footer on every page ----
  const range = doc.bufferedPageRange();
  for (let i = 0; i < range.count; i++) {
    doc.switchToPage(range.start + i);
    const fy = doc.page.height - 34;
    doc
      .fontSize(7)
      .fillColor(GREY)
      .font("Helvetica")
      .text(
        `Generated by the Fatalibuilders Construction App · ${profile} · Estimating figures for budgeting only — not a tender or fixed quotation. Engineering outputs require review by a licensed engineer.`,
        40,
        fy,
        { width: pageWidth - 40, align: "left" },
      );
    doc.text(`Page ${i + 1} of ${range.count}`, doc.page.width - 110, fy, {
      width: 70,
      align: "right",
    });
  }

  doc.end();
  return done;
}
