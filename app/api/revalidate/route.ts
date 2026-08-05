import { revalidatePath } from "next/cache";
import { NextRequest, NextResponse } from "next/server";

// Invalidates the complete dashboard layout and every child route.
// Called by GitHub Actions after an official benchmark run publishes results.
export async function POST(request: NextRequest) {
  const authorization = request.headers.get("authorization");
  const secret = process.env.REVALIDATE_SECRET;

  if (!secret) {
    return NextResponse.json({ error: "REVALIDATE_SECRET not configured" }, { status: 500 });
  }

  if (authorization !== `Bearer ${secret}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // All tabs consume release-bound artifacts; invalidating only `/` leaves
  // speed/parity/releases on an older ISR snapshot for up to 15 minutes.
  revalidatePath("/", "layout");

  return NextResponse.json({
    revalidated: true,
    timestamp: new Date().toISOString(),
  });
}
