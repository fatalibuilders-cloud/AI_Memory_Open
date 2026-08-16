/**
 * Upload validation for application documents.
 *
 * Public file upload is the largest attack surface on this site, so the rules
 * are deliberately narrow: three formats, checked by their actual leading
 * bytes rather than the browser-supplied content type, with a hard size cap.
 * Files are stored as bytes in the database and only ever served back to
 * signed-in staff, as attachments, with sniffing disabled.
 */

export const MAX_FILE_BYTES = 4 * 1024 * 1024; // 4 MB — see note on hosting limits below.
export const MAX_FILES_PER_APPLICATION = 8;

export type FileKind =
  | "title_deed"
  | "drawings"
  | "boq"
  | "approval"
  | "trust_certificate"
  | "site_photo"
  | "other";

export const FILE_KINDS: { kind: FileKind; label: string; hint: string; required: boolean }[] = [
  {
    kind: "title_deed",
    label: "Certified title deed",
    hint: "The certified copy showing who owns the land.",
    required: true,
  },
  {
    kind: "drawings",
    label: "Architectural drawings",
    hint: "Floor plans and elevations for the proposed masjid.",
    required: true,
  },
  {
    kind: "boq",
    label: "Bill of quantities",
    hint: "Priced BoQ, ideally prepared by a registered quantity surveyor.",
    required: true,
  },
  {
    kind: "approval",
    label: "County or council approval",
    hint: "Approved building permit, if you have it yet.",
    required: false,
  },
  {
    kind: "trust_certificate",
    label: "Trust or society registration",
    hint: "Registration certificate of the trust that holds the land.",
    required: false,
  },
  {
    kind: "site_photo",
    label: "Photo of the site",
    hint: "A photograph of the land or the current prayer space.",
    required: false,
  },
];

/** Accepted formats, identified by their magic bytes. */
const SIGNATURES: { contentType: string; extension: string; magic: number[] }[] = [
  { contentType: "application/pdf", extension: "pdf", magic: [0x25, 0x50, 0x44, 0x46] }, // %PDF
  { contentType: "image/jpeg", extension: "jpg", magic: [0xff, 0xd8, 0xff] },
  { contentType: "image/png", extension: "png", magic: [0x89, 0x50, 0x4e, 0x47] },
];

export const ACCEPTED_DESCRIPTION = "PDF, JPG or PNG, up to 4 MB each";

export class FileError extends Error {
  constructor(
    message: string,
    readonly status = 400,
  ) {
    super(message);
  }
}

export interface StoredFile {
  filename: string;
  contentType: string;
  bytes: Uint8Array;
}

/**
 * Validate one upload and normalise it for storage. The content type is
 * derived from the bytes, never from what the browser claimed.
 */
export function validateUpload(filename: string, bytes: Uint8Array): StoredFile {
  if (bytes.byteLength === 0) {
    throw new FileError(`${filename} is empty.`);
  }
  if (bytes.byteLength > MAX_FILE_BYTES) {
    throw new FileError(
      `${filename} is ${(bytes.byteLength / (1024 * 1024)).toFixed(1)} MB. The limit is 4 MB per file — send larger drawings to us by email and we will attach them.`,
    );
  }

  const match = SIGNATURES.find((signature) =>
    signature.magic.every((byte, i) => bytes[i] === byte),
  );
  if (!match) {
    throw new FileError(`${filename} is not a PDF, JPG or PNG file.`);
  }

  return { filename: safeFilename(filename, match.extension), contentType: match.contentType, bytes };
}

/**
 * Strip directory parts and anything exotic from a donor-supplied filename, so
 * it is safe to echo in the admin UI and in a Content-Disposition header.
 */
export function safeFilename(filename: string, extension: string): string {
  const base = filename.split(/[\\/]/).pop() ?? "document";
  const cleaned = base
    .replace(/\.[^.]*$/, "")
    .replace(/[^a-zA-Z0-9 ._-]/g, "")
    .trim()
    .slice(0, 80);
  return `${cleaned || "document"}.${extension}`;
}
