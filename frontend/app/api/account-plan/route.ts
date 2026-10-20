import { auth, currentUser } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

export async function GET() {
  const headers = { "Cache-Control": "private, no-store" };
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401, headers });
  try {
    const user = await currentUser();
    if (!user || user.id !== userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401, headers });
    return NextResponse.json({ user_id: userId, plan: user.publicMetadata.plan === "premium" ? "premium" : "free" }, { headers });
  } catch {
    return NextResponse.json({ error: "Plan unavailable" }, { status: 503, headers });
  }
}
