/**
 * Email provider boundary, mirroring the payments one: the app composes a
 * message and hands it over; which service actually delivers it is a
 * deployment detail.
 */

export interface EmailMessage {
  to: string;
  subject: string;
  html: string;
  text: string;
}

export interface EmailProvider {
  readonly name: string;
  /** False for the console logger used when no mail service is configured. */
  readonly live: boolean;
  send(message: EmailMessage): Promise<void>;
}
