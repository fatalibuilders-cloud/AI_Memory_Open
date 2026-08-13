import type { EmailMessage, EmailProvider } from "./provider";

/**
 * Resend over its REST API — no SDK dependency, same approach as the Stripe
 * adapter. The sending domain needs SPF and DKIM records or receipts land in
 * spam, which for a donation site means support tickets.
 */
export class ResendProvider implements EmailProvider {
  readonly name = "resend";
  readonly live = true;

  constructor(
    private readonly apiKey: string,
    private readonly from: string,
    private readonly replyTo: string | undefined,
    private readonly apiBase = "https://api.resend.com",
  ) {}

  async send(message: EmailMessage): Promise<void> {
    const res = await fetch(`${this.apiBase}/emails`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: this.from,
        to: [message.to],
        subject: message.subject,
        html: message.html,
        text: message.text,
        ...(this.replyTo ? { reply_to: this.replyTo } : {}),
      }),
    });

    if (!res.ok) {
      const body = (await res.json().catch(() => ({}))) as { message?: string };
      throw new Error(`Resend rejected the message: ${body.message ?? res.status}`);
    }
  }
}
