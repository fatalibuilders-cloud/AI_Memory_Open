/**
 * Organisation identity used on receipts and legal pages. Set these in the
 * environment at deploy time — the defaults are placeholders and are visibly
 * marked as such so an unconfigured deployment cannot pass itself off as a
 * registered charity.
 */
export interface Org {
  name: string;
  /** Registration number issued by the Kenyan authority the body is registered with. */
  registration: string;
  registrar: string;
  address: string;
  email: string;
  /** True once a real registration number is configured. */
  registered: boolean;
}

export function getOrg(): Org {
  const registration = process.env.ORG_REGISTRATION ?? "";
  return {
    name: process.env.ORG_NAME ?? "Masjid Fund",
    registration,
    registrar: process.env.ORG_REGISTRAR ?? "NGOs Co-ordination Board, Kenya",
    address: process.env.ORG_ADDRESS ?? "Address not yet configured",
    email: process.env.ORG_EMAIL ?? "salam@masjidfund.example",
    registered: registration.trim().length > 0,
  };
}

/**
 * Receipt footing. A Kenyan-registered body issues an acknowledgement of the
 * gift — it is not a US or UK tax-deduction receipt, and saying so plainly
 * keeps donors out of trouble with their own tax authorities.
 */
export function receiptNotice(org: Org): string {
  return org.registered
    ? `${org.name} is registered with the ${org.registrar} under ${org.registration}. This is an acknowledgement of your gift, not a tax-deduction receipt — donations are not deductible for US or UK tax purposes.`
    : `${org.name} has no registration number configured yet. This acknowledgement carries no tax status.`;
}
