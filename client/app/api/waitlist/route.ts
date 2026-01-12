import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function POST(req: Request) {
    try {
        const { email } = await req.json();

        if (!email || !email.includes("@")) {
            return NextResponse.json({ error: "Invalid email address" }, { status: 400 });
        }

        // For MVP, we save to a local CSV file
        // In production, you'd use a database like Supabase, Prisma, etc.
        const waitlistPath = path.join(process.cwd(), "waitlist.csv");
        const data = `${new Date().toISOString()},${email}\n`;

        fs.appendFileSync(waitlistPath, data);

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error("Waitlist error:", error);
        return NextResponse.json({ error: "Failed to save email" }, { status: 500 });
    }
}
