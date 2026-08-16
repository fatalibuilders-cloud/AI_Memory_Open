import { NextRequest, NextResponse } from "next/server";
import { DonationError } from "@/lib/donation";
import { createDonation } from "@/lib/donations";
import { PaymentError } from "@/lib/payments";
import { clientIp } from "@/lib/rate-limit";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}));
    const started = await createDonation(body, { ip: clientIp(req.headers) });
    return NextResponse.json(started, { status: 201 });
  } catch (err) {
    if (err instanceof DonationError || err instanceof PaymentError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    console.error("donation failed:", err);
    return NextResponse.json(
      { error: "We could not start this donation. Please try again." },
      { status: 500 },
    );
  }
}
