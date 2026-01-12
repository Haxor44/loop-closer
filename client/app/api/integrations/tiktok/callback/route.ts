import { NextRequest, NextResponse } from "next/server";

const TIKTOK_CLIENT_KEY = process.env.TIKTOK_CLIENT_KEY || "";
const TIKTOK_CLIENT_SECRET = process.env.TIKTOK_CLIENT_SECRET || "";
const TIKTOK_REDIRECT_URI = `${process.env.NEXTAUTH_URL}/api/integrations/tiktok/callback`;

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const error = searchParams.get("error");

    // Check for errors from TikTok
    if (error) {
        console.error("TikTok OAuth error:", error);
        return NextResponse.redirect(
            `${process.env.NEXTAUTH_URL}/dashboard/settings?integration=tiktok&status=error&message=${error}`
        );
    }

    // Verify state to prevent CSRF
    const storedState = request.cookies.get("tiktok_oauth_state")?.value;
    if (!state || state !== storedState) {
        return NextResponse.redirect(
            `${process.env.NEXTAUTH_URL}/dashboard/settings?integration=tiktok&status=error&message=invalid_state`
        );
    }

    if (!code) {
        return NextResponse.redirect(
            `${process.env.NEXTAUTH_URL}/dashboard/settings?integration=tiktok&status=error&message=no_code`
        );
    }

    try {
        // Exchange code for access token
        const tokenResponse = await fetch("https://open.tiktokapis.com/v2/oauth/token/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams({
                client_key: TIKTOK_CLIENT_KEY,
                client_secret: TIKTOK_CLIENT_SECRET,
                code: code,
                grant_type: "authorization_code",
                redirect_uri: TIKTOK_REDIRECT_URI,
            }),
        });

        const tokenData = await tokenResponse.json();

        if (tokenData.error) {
            console.error("TikTok token error:", tokenData);
            return NextResponse.redirect(
                `${process.env.NEXTAUTH_URL}/dashboard/settings?integration=tiktok&status=error&message=${tokenData.error.code}`
            );
        }

        // TODO: Store the access token in your database linked to the user
        // For now, we'll just log it and redirect with success
        console.log("TikTok tokens received:", {
            access_token: tokenData.access_token ? "***" : "missing",
            refresh_token: tokenData.refresh_token ? "***" : "missing",
            expires_in: tokenData.expires_in,
            open_id: tokenData.open_id,
        });

        // Store integration status - you'll want to save this to your backend
        // For now, redirect with success
        const response = NextResponse.redirect(
            `${process.env.NEXTAUTH_URL}/dashboard/settings?integration=tiktok&status=success`
        );

        // Clear the state cookie
        response.cookies.delete("tiktok_oauth_state");

        return response;
    } catch (error) {
        console.error("TikTok token exchange error:", error);
        return NextResponse.redirect(
            `${process.env.NEXTAUTH_URL}/dashboard/settings?integration=tiktok&status=error&message=token_exchange_failed`
        );
    }
}
