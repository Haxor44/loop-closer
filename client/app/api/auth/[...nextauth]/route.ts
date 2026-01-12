import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import RedditProvider from "next-auth/providers/reddit";
import TwitterProvider from "next-auth/providers/twitter";

const handler = NextAuth({
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
});

export { handler as GET, handler as POST };
