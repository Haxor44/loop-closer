"use client";

import Sidebar from "@/components/Dashboard/Sidebar";
import { useSession, signIn } from "next-auth/react";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";

interface IntegrationStatus {
    reddit: boolean;
    tiktok: boolean;
    twitter: boolean;
    instagram: boolean;
    facebook: boolean;
    jira: boolean;
}

function SettingsContent() {
    const { data: session } = useSession();
    const [plan, setPlan] = useState("Free");
    const searchParams = useSearchParams();
    const [integrations, setIntegrations] = useState<IntegrationStatus>({
        reddit: false,
        tiktok: false,
        twitter: false,
        instagram: false,
        facebook: false,
        jira: false,
    });
    const [notification, setNotification] = useState<{ type: string; message: string } | null>(null);

    useEffect(() => {
        if (session?.user?.email) {
            // 1. Sync User with Backend
            fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/sync`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: session.user.email, name: session.user.name })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.user) setPlan(data.user.plan);
                });

            // TODO: Fetch integration status from backend
        }
    }, [session]);

    // Handle OAuth callback notifications
    useEffect(() => {
        const integration = searchParams.get("integration");
        const status = searchParams.get("status");
        const payment = searchParams.get("payment");

        if (integration && status) {
            if (status === "success") {
                setIntegrations(prev => ({ ...prev, [integration]: true }));
                setNotification({ type: "success", message: `${integration} connected successfully!` });
            } else {
                setNotification({ type: "error", message: `Failed to connect ${integration}` });
            }
            // Clear URL params
            window.history.replaceState({}, "", "/dashboard/settings");
        }

        if (payment === "success") {
            setPlan("Pro");
            setNotification({ type: "success", message: "Payment successful! Welcome to Pro!" });
            window.history.replaceState({}, "", "/dashboard/settings");
        }
    }, [searchParams]);

    const handleUpgrade = async () => {
        if (!session?.user?.email) return;

        try {
            console.log("Initiating payment for:", session.user.email);
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/payment/upgrade`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: session.user.email })
            });

            const data = await res.json();
            console.log("Payment response:", data);

            if (res.ok && data.payment_url) {
                window.location.href = data.payment_url;
            } else {
                alert("Payment initiation failed: " + (data.detail || JSON.stringify(data)));
            }
        } catch (error) {
            console.error("Payment Error:", error);
            alert("Payment connection failed. Check console for details.");
        }
    };

    const handleConnect = (platform: string) => {
        switch (platform) {
            case "reddit":
                // Use NextAuth's built-in Reddit provider
                signIn("reddit", { callbackUrl: "/dashboard/settings?integration=reddit&status=success" });
                break;
            case "tiktok":
                // Use custom TikTok OAuth flow
                window.location.href = "/api/integrations/tiktok/auth";
                break;
            case "twitter":
                // Use NextAuth's built-in Twitter provider
                signIn("twitter", { callbackUrl: "/dashboard/settings?integration=twitter&status=success" });
                break;
            case "instagram":
            case "facebook":
                // Meta platforms - placeholder
                alert(`${platform} integration requires Meta Business API setup. Coming soon!`);
                break;
            case "jira":
                if (plan === "Pro") {
                    alert("Jira integration coming soon!");
                }
                break;
        }
    };

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto p-8 pt-12">
                <div className="max-w-2xl mx-auto">
                    <h1 className="text-3xl font-bold mb-8">Settings</h1>

                    {/* Notification Banner */}
                    {notification && (
                        <div className={`mb-6 p-4 rounded-lg ${notification.type === "success" ? "bg-green-500/20 border border-green-500/50 text-green-400" : "bg-red-500/20 border border-red-500/50 text-red-400"}`}>
                            {notification.message}
                            <button onClick={() => setNotification(null)} className="float-right">✕</button>
                        </div>
                    )}

                    <div className="space-y-6">
                        {/* Profile Section */}
                        <div className="glass-card p-6 border-primary/10">
                            <h2 className="text-xl font-bold mb-4 flex justify-between items-center">
                                Profile
                                <span className={`text-xs px-2 py-1 rounded border ${plan === 'Pro' ? 'bg-blue-500/20 text-blue-400 border-blue-500/50' : 'bg-secondary text-muted'}`}>
                                    {plan.toUpperCase()} PLAN
                                </span>
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1 text-muted">Email</label>
                                    <input type="email" value={session?.user?.email || ""} disabled className="w-full bg-secondary/30 border border-border rounded-lg px-4 py-2 text-sm opacity-50" />
                                </div>
                                <button className="px-4 py-2 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary/90 transition-colors">
                                    Update Profile
                                </button>
                            </div>
                        </div>

                        {/* Monitoring Configuration */}
                        <div className="glass-card p-6 border-primary/10">
                            <h2 className="text-xl font-bold mb-4">Monitoring Configuration</h2>
                            <p className="text-sm text-muted mb-4">Tell the agent where to listen for feedback across all platforms.</p>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Global Keywords / Brand Terms</label>
                                    <input type="text" placeholder="e.g. 'Loop Closer', 'Customer Service AI'" className="w-full bg-secondary/30 border border-border rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-primary" />
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Reddit Subreddits</label>
                                        <input type="text" placeholder="e.g. r/saas, r/tech" className="w-full bg-secondary/30 border border-border rounded-lg px-4 py-2 text-sm" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Instagram Hashtags</label>
                                        <input type="text" placeholder="e.g. #aiagent, #customerservice" className="w-full bg-secondary/30 border border-border rounded-lg px-4 py-2 text-sm" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">TikTok Keywords</label>
                                        <input type="text" placeholder="e.g. 'bad service loop'" className="w-full bg-secondary/30 border border-border rounded-lg px-4 py-2 text-sm" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Facebook Page URL</label>
                                        <input type="text" placeholder="https://facebook.com/..." className="w-full bg-secondary/30 border border-border rounded-lg px-4 py-2 text-sm" />
                                    </div>
                                </div>
                                <div className="pt-2">
                                    <button className="px-4 py-2 bg-secondary border border-border text-foreground hover:bg-card transition-colors rounded-lg text-sm">
                                        Save Configuration
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Integration Section */}
                        <div className="glass-card p-6 border-primary/10">
                            <h2 className="text-xl font-bold mb-4">Integrations</h2>
                            <div className="space-y-4">
                                {/* Reddit */}
                                <div className="flex items-center justify-between p-4 bg-secondary/20 rounded-lg">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-[#FF4500] flex items-center justify-center font-bold text-white text-xs">R</div>
                                        <div>
                                            <p className="font-medium">Reddit</p>
                                            <p className={`text-xs ${integrations.reddit ? "text-green-400" : "text-muted"}`}>
                                                {integrations.reddit ? "Connected" : "Not Connected"}
                                            </p>
                                        </div>
                                    </div>
                                    {integrations.reddit ? (
                                        <button className="text-xs text-muted hover:text-foreground">Configure</button>
                                    ) : (
                                        <button onClick={() => handleConnect("reddit")} className="px-3 py-1 bg-secondary hover:bg-border border border-border rounded text-xs">Connect</button>
                                    )}
                                </div>

                                {/* TikTok */}
                                <div className="flex items-center justify-between p-4 bg-secondary/20 rounded-lg">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-black flex items-center justify-center font-bold text-white text-xs">T</div>
                                        <div>
                                            <p className="font-medium">TikTok</p>
                                            <p className={`text-xs ${integrations.tiktok ? "text-green-400" : "text-muted"}`}>
                                                {integrations.tiktok ? "Connected" : "Not Connected"}
                                            </p>
                                        </div>
                                    </div>
                                    {integrations.tiktok ? (
                                        <button className="text-xs text-muted hover:text-foreground">Configure</button>
                                    ) : (
                                        <button onClick={() => handleConnect("tiktok")} className="px-3 py-1 bg-secondary hover:bg-border border border-border rounded text-xs">Connect</button>
                                    )}
                                </div>

                                {/* X (Twitter) */}
                                <div className="flex items-center justify-between p-4 bg-secondary/20 rounded-lg">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-black flex items-center justify-center font-bold text-white text-xs">𝕏</div>
                                        <div>
                                            <p className="font-medium">X (Twitter)</p>
                                            <p className={`text-xs ${integrations.twitter ? "text-green-400" : "text-muted"}`}>
                                                {integrations.twitter ? "Connected" : "Not Connected"}
                                            </p>
                                        </div>
                                    </div>
                                    {integrations.twitter ? (
                                        <button className="text-xs text-muted hover:text-foreground">Configure</button>
                                    ) : (
                                        <button onClick={() => handleConnect("twitter")} className="px-3 py-1 bg-secondary hover:bg-border border border-border rounded text-xs">Connect</button>
                                    )}
                                </div>

                                {/* Instagram */}
                                <div className="flex items-center justify-between p-4 bg-secondary/20 rounded-lg">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-gradient-to-tr from-yellow-400 via-red-500 to-purple-500 flex items-center justify-center font-bold text-white text-xs">I</div>
                                        <div>
                                            <p className="font-medium">Instagram</p>
                                            <p className={`text-xs ${integrations.instagram ? "text-green-400" : "text-muted"}`}>
                                                {integrations.instagram ? "Connected" : "Not Connected"}
                                            </p>
                                        </div>
                                    </div>
                                    <button onClick={() => handleConnect("instagram")} className="px-3 py-1 bg-secondary hover:bg-border border border-border rounded text-xs">Connect</button>
                                </div>

                                {/* Facebook */}
                                <div className="flex items-center justify-between p-4 bg-secondary/20 rounded-lg">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center font-bold text-white text-xs">F</div>
                                        <div>
                                            <p className="font-medium">Facebook</p>
                                            <p className={`text-xs ${integrations.facebook ? "text-green-400" : "text-muted"}`}>
                                                {integrations.facebook ? "Connected" : "Not Connected"}
                                            </p>
                                        </div>
                                    </div>
                                    <button onClick={() => handleConnect("facebook")} className="px-3 py-1 bg-secondary hover:bg-border border border-border rounded text-xs">Connect</button>
                                </div>

                                {/* Jira (Up sell) */}
                                <div className={`flex items-center justify-between p-4 bg-secondary/20 rounded-lg ${plan === 'Free' ? 'opacity-75' : ''}`}>
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-blue-500 flex items-center justify-center font-bold text-white text-xs">J</div>
                                        <div>
                                            <p className="font-medium">Jira</p>
                                            <p className="text-xs text-muted">{plan === 'Pro' ? 'Ready to Connect' : 'Teams Plan Required'}</p>
                                        </div>
                                    </div>
                                    {plan === 'Pro' ? (
                                        <button onClick={() => handleConnect("jira")} className="px-3 py-1 bg-secondary hover:bg-border border border-border rounded text-xs">Connect</button>
                                    ) : (
                                        <button onClick={handleUpgrade} className="px-3 py-1 bg-gradient-to-r from-yellow-500 to-amber-600 text-white font-bold text-xs rounded shadow-lg shadow-amber-500/20 hover:scale-105 transition-transform">
                                            Upgrade to Teams 🔒
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default function SettingsPage() {
    return (
        <Suspense fallback={
            <div className="flex h-screen bg-background text-foreground items-center justify-center">
                <div className="animate-pulse">Loading settings...</div>
            </div>
        }>
            <SettingsContent />
        </Suspense>
    );
}
