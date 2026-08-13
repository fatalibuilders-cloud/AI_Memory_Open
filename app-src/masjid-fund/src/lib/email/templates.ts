import { INTENT_LABELS } from "@/lib/donation";
import type { Donation } from "@/lib/donations";
import { formatMoney } from "@/lib/money";
import { receiptNotice, type Org } from "@/lib/org";
import type { EmailMessage } from "./provider";

/**
 * Receipt and cancellation emails. Written as inline-styled HTML with a plain
 * text twin — mail clients strip stylesheets, and some donors read in text.
 */

export function receiptEmail(
  donation: Donation,
  org: Org,
  links: { manageUrl: string | null; projectUrl: string | null },
): EmailMessage {
  const amount = `${formatMoney(donation.amountCents, donation.currency)}${
    donation.frequency === "monthly" ? " each month" : ""
  }`;
  const destination = donation.projectName ?? "the masjid most in need of funds";
  const greeting = donation.donorName ? `Assalamu alaikum ${donation.donorName},` : "Assalamu alaikum,";

  const rows: [string, string][] = [
    ["Reference", donation.reference],
    ["Amount", amount],
    ["Type", INTENT_LABELS[donation.intent]],
    ["Goes to", destination],
    ["Received", new Date(donation.completedAt ?? donation.createdAt).toUTCString()],
  ];
  if (donation.dedication) rows.push(["Dedication", donation.dedication]);

  const text = [
    greeting,
    "",
    `Your donation of ${amount} towards ${destination} has been received. Jazak Allahu khayran.`,
    "",
    ...rows.map(([label, value]) => `${label}: ${value}`),
    "",
    links.projectUrl ? `Follow the build: ${links.projectUrl}` : "",
    links.manageUrl
      ? `Manage or cancel your monthly giving at any time: ${links.manageUrl}`
      : "",
    "",
    receiptNotice(org),
    `${org.name} · ${org.address} · ${org.email}`,
  ]
    .filter(Boolean)
    .join("\n");

  const html = layout(
    org,
    `
    <p style="margin:0 0 16px">${escapeHtml(greeting)}</p>
    <p style="margin:0 0 24px">Your donation of <strong>${escapeHtml(amount)}</strong> towards
      ${escapeHtml(destination)} has been received. Jazak Allahu khayran — may Allah accept it
      from you and make it a lasting sadaqah.</p>
    ${table(rows)}
    ${
      links.projectUrl
        ? `<p style="margin:24px 0 0"><a href="${links.projectUrl}" style="background:#175943;color:#faf8f3;padding:12px 20px;border-radius:10px;text-decoration:none;display:inline-block">Follow the build</a></p>`
        : ""
    }
    ${
      links.manageUrl
        ? `<p style="margin:24px 0 0;font-size:14px;color:#6f6650">You can pause or cancel your monthly giving at any time from
             <a href="${links.manageUrl}" style="color:#175943">this link</a>. Keep this email — the link is your access to it.</p>`
        : ""
    }
  `,
  );

  return {
    to: donation.donorEmail,
    subject: `Your donation ${donation.reference} — ${amount}`,
    html,
    text,
  };
}

export function cancellationEmail(donation: Donation, org: Org): EmailMessage {
  const amount = formatMoney(donation.amountCents, donation.currency);
  const text = [
    donation.donorName ? `Assalamu alaikum ${donation.donorName},` : "Assalamu alaikum,",
    "",
    `Your monthly gift of ${amount} (reference ${donation.reference}) has been cancelled. Nothing further will be charged.`,
    "",
    "Donations already made stay with the project they were given to.",
    "",
    `${org.name} · ${org.address} · ${org.email}`,
  ].join("\n");

  return {
    to: donation.donorEmail,
    subject: `Monthly giving cancelled — ${donation.reference}`,
    html: layout(
      org,
      `
      <p style="margin:0 0 16px">${escapeHtml(
        donation.donorName ? `Assalamu alaikum ${donation.donorName},` : "Assalamu alaikum,",
      )}</p>
      <p style="margin:0 0 16px">Your monthly gift of <strong>${escapeHtml(amount)}</strong>
        (reference ${escapeHtml(donation.reference)}) has been cancelled. Nothing further will
        be charged.</p>
      <p style="margin:0;color:#6f6650">Donations already made stay with the project they were
        given to, and the build continues.</p>
    `,
    ),
    text,
  };
}

function layout(org: Org, body: string): string {
  return `<!doctype html>
<html><body style="margin:0;background:#faf8f3;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#0c3227">
  <div style="max-width:560px;margin:0 auto;padding:32px 20px">
    <p style="margin:0 0 24px;font-size:20px;font-weight:600;color:#114535">${escapeHtml(org.name)}</p>
    <div style="background:#ffffff;border:1px solid #e7e0cd;border-radius:16px;padding:28px;line-height:1.6">
      ${body}
    </div>
    <p style="margin:20px 0 0;font-size:12px;color:#6f6650;line-height:1.6">
      ${escapeHtml(receiptNotice(org))}<br>
      ${escapeHtml(org.name)} · ${escapeHtml(org.address)} · ${escapeHtml(org.email)}
    </p>
  </div>
</body></html>`;
}

function table(rows: [string, string][]): string {
  const cells = rows
    .map(
      ([label, value]) =>
        `<tr>
           <td style="padding:8px 0;color:#6f6650;font-size:14px">${escapeHtml(label)}</td>
           <td style="padding:8px 0;text-align:right;font-weight:600">${escapeHtml(value)}</td>
         </tr>`,
    )
    .join("");
  return `<table style="width:100%;border-collapse:collapse;border-top:1px solid #e7e0cd">${cells}</table>`;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
