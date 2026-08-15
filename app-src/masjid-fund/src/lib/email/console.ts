import type { EmailMessage, EmailProvider } from "./provider";

/**
 * Fallback when no mail service is configured: the message is logged rather
 * than sent, and still recorded in email_log so the admin screens show what
 * a donor would have received.
 */
export class ConsoleProvider implements EmailProvider {
  readonly name = "console";
  readonly live = false;

  async send(message: EmailMessage): Promise<void> {
    // The plain-text body is printed too, so that while testing you can read
    // the receipt — and follow the monthly-giving link it carries — without a
    // mail service. Production always has a real provider configured.
    console.info(
      [
        `[email:not-sent] to=${message.to}`,
        `subject: ${message.subject}`,
        message.text,
        "[end of message]",
      ].join("\n"),
    );
  }
}
