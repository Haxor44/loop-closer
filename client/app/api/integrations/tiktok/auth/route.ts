import { NextRequest, NextResponse } from "next/server";

// TikTok OAuth2 Configuration
const TIKTOK_CLIENT_KEY = process.env.TIKTOK_CLIENT_KEY || "";
const TIKTOK_REDIRECT_URI = `${process.env.NEXTAUTH_URL}/api/integrations/tiktok/callback`;

export async function GET(request: NextRequest) {
    // Generate a random state for CSRF protection
    const state = Math.random().toString(36).substring(2, 15);

    // TikTok OAuth2 authorization URL
    const authUrl = new URL("https://www.tiktok.com/v2/auth/authorize/");
    authUrl.searchParams.set("client_key", TIKTOK_CLIENT_KEY);
    authUrl.searchParams.set("scope", "user.info.basic,video.list");
    authUrl.searchParams.set("response_type", "code");
    authUrl.searchParams.set("redirect_uri", TIKTOK_REDIRECT_URI);
    authUrl.searchParams.set("state", state);

    // Store state in cookie for verification on callback
    const response = NextResponse.redirect(authUrl.toString());
    response.cookies.set("tiktok_oauth_state", state, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        maxAge: 60 * 10, // 10 minutes
    });

    return response;
}
