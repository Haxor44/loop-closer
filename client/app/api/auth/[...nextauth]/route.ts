import NextAuth, { AuthOptions } from "next-auth";
import { getServerSession } from "next-auth/next";
import GoogleProvider from "next-auth/providers/google";
import RedditProvider from "next-auth/providers/reddit";
import TwitterProvider from "next-auth/providers/twitter";

export const authOptions: AuthOptions = {
    providers: [
        GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID || "",
            clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
        }),
        RedditProvider({
            clientId: process.env.REDDIT_CLIENT_ID || "",
            clientSecret: process.env.REDDIT_CLIENT_SECRET || "",
            authorization: {
                params: {
                    duration: "permanent",
                },
            },
        }),
        TwitterProvider({
            clientId: process.env.TWITTER_CLIENT_ID || "",
            clientSecret: process.env.TWITTER_CLIENT_SECRET || "",
            version: "2.0", // Use OAuth 2.0
        }),
    ],
    callbacks: {
        async signIn({ user, account, profile }) {
            console.log("🔵 DEBUG: SignIn callback triggered for provider:", account?.provider);

            let currentUserEmail = null;
            try {
                // Get current session to see if user is already logged in
                const session = await getServerSession(authOptions);
                currentUserEmail = session?.user?.email;
                console.log("🔵 DEBUG: Current session email:", currentUserEmail);
            } catch (error) {
                console.error("🔴 DEBUG: Error getting server session:", error);
            }

            // Handle Twitter connection
            if (account?.provider === "twitter" && account.access_token) {
                // If user is already logged in, use THEIR email, otherwise use the one from Twitter (if any)
                const targetEmail = currentUserEmail || user.email;
                console.log("🔵 DEBUG: Target email for Twitter connection:", targetEmail);

                if (targetEmail) {
                    try {
                        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/twitter-tokens`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                email: targetEmail,
                                access_token: account.access_token,
                                refresh_token: account.refresh_token,
                                expires_at: account.expires_at
                            })
                        });
                        console.log('✅ Twitter tokens stored for', targetEmail);

                        // CRITICAL: If we are already logged in, DO NOT let NextAuth switch the session.
                        // Return the redirect URL to settings page directly.
                        // This "aborts" the sign-in but we've already saved the tokens.
                        if (currentUserEmail) {
                            console.log("🔵 DEBUG: Redirecting back to settings to preserve session");
                            return "/dashboard/settings?integration=twitter&status=success";
                        }
                    } catch (error) {
                        console.error('❌ Failed to store Twitter tokens:', error);
                    }
                } else {
                    console.log("🔴 DEBUG: No email found for Twitter connection");
                }
            }

            // Handle Reddit connection
            if (account?.provider === "reddit" && currentUserEmail) {
                // For Reddit, we also want to preserve the session if likely used for linking
                // (Though currently we might rely on the sign in behavior, let's keep it safe)
                return "/dashboard/settings?integration=reddit&status=success";
            }

            return true;
        },
        async session({ session, token }) {
            // Add custom claims or role logic here later
            return session;
        },
        async jwt({ token, account }) {
            // Persist the OAuth access_token to the token right after signin
            if (account) {
                token.accessToken = account.access_token;
                token.provider = account.provider;
            }
            return token;
        },
    },
    pages: {
        signIn: "/auth/signin", // Custom sign-in page (optional)
    },
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
