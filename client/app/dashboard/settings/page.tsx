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
    const [isLoadingUser, setIsLoadingUser] = useState(true);

    const [config, setConfig] = useState({
        keywords: "",
        subreddits: "",
        twitter_keywords: "",
        product_name: "",
        brand_voice: ""
    });

    const [twitterQuota, setTwitterQuota] = useState({
        searches_today: 0,
        tweets_today: 0,
        searches_limit: 0,
        tweets_limit: 0,
        last_reset: ""
    });

    useEffect(() => {
        if (session?.user?.email) {
            // 1. Sync User with Backend & Get Config
            const apiUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/users/sync`;
            console.log("Syncing user to:", apiUrl);
            console.log("VERSION_CHECK: v4_FIXED_URLS");

            fetch(apiUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache"
                },
                body: JSON.stringify({ email: session.user.email, name: session.user.name }),
                cache: "no-store"
            })
                .then(res => res.json())
                .then(data => {
                    if (data.user) {
                        setPlan(data.user.plan);
                        if (data.user.name) {
                            console.log("Setting name from DB:", data.user.name);
                            setName(data.user.name); // Always trust DB over session
                        }
                        if (data.user.config) {
                            setConfig({
                                keywords: data.user.config.keywords || "",
                                subreddits: data.user.config.subreddits || "",
                                twitter_keywords: data.user.config.twitter_keywords || "",
                                product_name: data.user.config.product_name || "",
                                brand_voice: data.user.config.brand_voice || ""
                            });
                        }
                        // Restore connected platforms
                        if (data.user.connected_platforms) {
                            const newIntegrations = { ...integrations };
                            data.user.connected_platforms.forEach((p: string) => {
                                if (p in newIntegrations) {
                                    newIntegrations[p as keyof IntegrationStatus] = true;
                                }
                            });
                            setIntegrations(newIntegrations);
                        }
                    }
                })
                .finally(() => setIsLoadingUser(false));
        }
    }, [session]);

    // Fetch Twitter quota
    useEffect(() => {
        const fetchQuota = async () => {
            if (session?.user?.email && integrations.twitter) {
                try {
                    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/twitter-quota`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email: session.user.email })
                    });
                    const data = await res.json();
                    if (data.quota) {
                        setTwitterQuota(data.quota);
                    }
                } catch (error) {
                    console.error("Error fetching quota:", error);
                }
            }
        };
        fetchQuota();
    }, [session, integrations.twitter]);

    // Handle form changes
    const handleConfigChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setConfig(prev => ({ ...prev, [name]: value }));
    };

    const [name, setName] = useState("");

    useEffect(() => {
        // Only set name from session if we haven't fetched it yet
        if (session?.user?.name && !name) setName(session.user.name);
    }, [session]);

    // ... (inside useEffect for backend sync, update name if needed)

    // ...

    const handleUpdateProfile = async () => {
        if (!session?.user?.email) return;

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/profile`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email: session.user.email,
                    name: name // Use state name
                })
            });

            if (res.ok) {
                setNotification({ type: "success", message: "Profile updated successfully!" });
                setTimeout(() => setNotification(null), 3000);
            } else {
                setNotification({ type: "error", message: "Failed to update profile" });
            }
        } catch (error) {
            setNotification({ type: "error", message: "Error updating profile" });
        }
    };

    const [isSavingConfig, setIsSavingConfig] = useState(false);
    const [isSaved, setIsSaved] = useState(false);

    const handleSaveConfig = async () => {
        if (!session?.user?.email) return;
        setIsSavingConfig(true);

        try {
            // Hardcode URL to match other fixes
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/config`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email: session.user.email,
                    ...config
                })
            });

            if (res.ok) {
                setIsSaved(true);
                setNotification({ type: "success", message: "Configuration saved successfully!" });
                setTimeout(() => setNotification(null), 3000);
                setTimeout(() => setIsSaved(false), 2000);
            } else {
                const data = await res.json();
                setNotification({ type: "error", message: data.detail || "Failed to save configuration" });
            }
        } catch (error) {
            setNotification({ type: "error", message: "Error saving configuration" });
        } finally {
            setIsSavingConfig(false);
        }
    };

    const updateIntegrationStatus = async (platform: string, connected: boolean) => {
        if (!session?.user?.email) return;
        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/integrations`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email: session.user.email,
                    platform,
                    connected
                })
            });
        } catch (error) {
            console.error("Failed to persist integration status", error);
        }
    };

    // Handle OAuth callback notifications
    useEffect(() => {
        const integration = searchParams.get("integration");
        const status = searchParams.get("status");
        const payment = searchParams.get("payment");

        if (integration && status) {
            if (status === "success") {
                setIntegrations(prev => ({ ...prev, [integration]: true }));
                setNotification({ type: "success", message: `${integration} connected successfully!` });
                updateIntegrationStatus(integration, true);
            } else {
                setNotification({ type: "error", message: `Failed to connect ${integration}` });
            }
            // Clear URL params
            window.history.replaceState({}, "", "/dashboard/settings");
        }

        // Handle PesaPal callback (comes with OrderTrackingId)
        const orderTrackingId = searchParams.get("OrderTrackingId");
        if (orderTrackingId && session?.user?.email) {
            // Close modal if open
            setShowPaymentModal(false);

            // Verify payment status with backend
            fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/payment/verify?OrderTrackingId=${orderTrackingId}`)
                .then(res => res.json())
                .then(data => {
                    console.log("Payment verification response:", data);
                    if (data.status === "success" && data.payment_status === "COMPLETED") {
                        setPlan("Pro");
                        setNotification({ type: "success", message: "Payment successful! Welcome to Pro!" });
                    } else if (data.status === "pending") {
                        setNotification({ type: "info", message: "Payment is being processed..." });
                    } else {
                        setNotification({ type: "error", message: "Payment verification failed. Please contact support." });
                    }
                })
                .catch(error => {
                    console.error("Payment verification error:", error);
                    setNotification({ type: "error", message: "Failed to verify payment" });
                });

            // Clear URL params
            window.history.replaceState({}, "", "/dashboard/settings");
        }

        // Legacy payment success handler (for backward compatibility)
        if (payment === "success") {
            setShowPaymentModal(false);
            setPlan("Pro");
            setNotification({ type: "success", message: "Payment successful! Welcome to Pro!" });
            window.history.replaceState({}, "", "/dashboard/settings");
        }
    }, [searchParams, session]); // Added session to dependencies

    const [isUpgrading, setIsUpgrading] = useState(false);
    const [showPaymentModal, setShowPaymentModal] = useState(false);
    const [paymentUrl, setPaymentUrl] = useState("");

    const handleUpgrade = async () => {
        if (!session?.user?.email) return;
        setIsUpgrading(true);

        try {
            console.log("Initiating payment for:", session.user.email);
            // Hardcode URL to match other fixes
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/payment/upgrade`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: session.user.email })
            });

            const data = await res.json();
            if (data.payment_url) {
                // Open modal instead of redirect
                setPaymentUrl(data.payment_url);
                setShowPaymentModal(true);
                setIsUpgrading(false);
            } else {
                setIsUpgrading(false);
            }
        } catch (error) {
            console.error("Payment error:", error);
            setIsUpgrading(false);
            setNotification({ type: "error", message: "Failed to initiate payment" });
        }
    };

    // ...

    {
        plan === 'Free' && (
            <button
                onClick={handleUpgrade}
                disabled={isUpgrading}
                className={`px-3 py-1 bg-gradient-to-r from-blue-600 to-violet-600 text-white text-xs font-bold rounded shadow-lg shadow-blue-500/20 transition-transform ${isUpgrading ? "opacity-75 cursor-wait" : "hover:scale-105"}`}
            >
                {isUpgrading ? "Processing..." : "Upgrade to Pro"}
            </button>
        )
    }
    const handleConnect = (service: string) => {
        if (service === "reddit") {
            signIn("reddit", { callbackUrl: "/dashboard/settings?integration=reddit&status=success" });
        } else if (service === "tiktok") {
            window.location.href = "/api/integrations/tiktok/auth";
        } else if (service === "twitter") {
            signIn("twitter", { callbackUrl: "/dashboard/settings?integration=twitter&status=success" });
        } else if (service === "instagram" || service === "facebook") {
            alert(`${service} integration requires Meta Business API setup. Coming soon!`);
        } else if (service === "jira") {
            if (plan === "Pro") {
                alert("Jira integration coming soon!");
            }
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
                                <div className="flex items-center gap-2">
                                    {isLoadingUser ? (
                                        <div className="h-6 w-24 bg-secondary/50 animate-pulse rounded"></div>
                                    ) : (
                                        <>
                                            <span className={`text-xs px-2 py-1 rounded border ${plan === 'Pro' ? 'bg-blue-500/20 text-blue-400 border-blue-500/50' : 'bg-secondary text-muted'}`}>
                                                {plan.toUpperCase()} PLAN
                                            </span>
                                            {plan === 'Free' && (
                                                <button
                                                    onClick={handleUpgrade}
                                                    disabled={isUpgrading}
                                                    className={`px-3 py-1 bg-gradient-to-r from-blue-600 to-violet-600 text-white text-xs font-bold rounded shadow-lg shadow-blue-500/20 transition-transform ${isUpgrading ? "opacity-75 cursor-wait" : "hover:scale-105"}`}
                                                >
                                                    {isUpgrading ? "Processing..." : "Upgrade to Pro"}
                                                </button>
                                            )}
                                        </>
                                    )}
                                </div>
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1 text-muted">Full Name</label>
                                    <input
                                        type="text"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        className="w-full bg-secondary/30 border border-border rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-primary"
                                        placeholder="Your Name"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1 text-muted">Email</label>
                                    <input type="email" value={session?.user?.email || ""} disabled className="w-full bg-secondary/30 border border-border rounded-lg px-4 py-2 text-sm opacity-50" />
                                </div>
                                <button
                                    onClick={handleUpdateProfile}
                                    className="px-4 py-2 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary/90 transition-colors">
                                    Update Profile
                                </button>
                            </div>
                        </div>

                        {/* Monitoring Configuration */}
                        <div id="monitoring-config" className="glass-card p-6 border-primary/10">
                            <h2 className="text-xl font-bold mb-4">Monitoring Configuration</h2>
                            <p className="text-sm text-muted mb-4">Tell the agent where to listen for feedback across all platforms.</p>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Product Name (for filtering)</label>
                                    <input
                                        type="text"
                                        name="product_name"
                                        value={config.product_name}
                                        onChange={handleConfigChange}
                                        placeholder="e.g. Loop Closer"
                                        className="w-full bg-secondary/30 border border-border rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-primary mb-2"
                                    />
                                    <p className="text-xs text-muted">We will only analyze posts that explicitly mention this name, to reduce noise.</p>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Global Keywords / Brand Terms</label>
                                    <input
                                        type="text"
                                        name="keywords"
                                        value={config.keywords}
                                        onChange={handleConfigChange}
                                        placeholder="e.g. customer service ai, help desk"
                                        className="w-full bg-secondary/30 border border-border rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-primary"
                                    />
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Reddit Subreddits</label>
                                        <input
                                            type="text"
                                            name="subreddits"
                                            value={config.subreddits}
                                            onChange={handleConfigChange}
                                            placeholder="e.g. r/saas, r/tech"
                                            className="w-full bg-secondary/30 border border-border rounded-lg px-4 py-2 text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Twitter Search Terms</label>
                                        <input
                                            type="text"
                                            name="twitter_keywords"
                                            value={config.twitter_keywords}
                                            onChange={handleConfigChange}
                                            placeholder="e.g. 'competitor name', 'industry news'"
                                            className="w-full bg-secondary/30 border border-border rounded-lg px-4 py-2 text-sm"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Brand Voice (for AI replies)</label>
                                    <div className="flex flex-wrap gap-2 mb-2 mt-2">
                                        {[
                                            { label: "Professional", prompt: "Write a polite, formal, and solution-oriented response that maintains a corporate standard." },
                                            { label: "Empathetic", prompt: "Respond with deep understanding and care, validating the user's feelings first." },
                                            { label: "Direct", prompt: "Be concise and straight to the point. Focus purely on the solution without fluff." },
                                            { label: "Noir", prompt: "Use a moody, premium, and slightly mysterious tone. Keep it cool and sophisticated." },
                                            { label: "Vibrant", prompt: "Use high energy, emojis, and an enthusiastic tone. Make the user feel excited!" },
                                            { label: "Soft", prompt: "Use gentle language, soft phrasing, and a very approachable, non-threatening tone." }
                                        ].map((item) => (
                                            <button
                                                key={item.label}
                                                type="button"
                                                onClick={() => setConfig(prev => ({ ...prev, brand_voice: item.prompt }))}
                                                className={`px-3 py-1 rounded-full text-xs transition-colors border ${config.brand_voice === item.prompt
                                                    ? "bg-primary text-white border-primary"
                                                    : "bg-secondary/50 hover:bg-primary/20 hover:text-primary border-border"
                                                    }`}
                                            >
                                                {item.label}
                                            </button>
                                        ))}
                                    </div>
                                    <textarea
                                        name="brand_voice"
                                        value={config.brand_voice}
                                        onChange={handleConfigChange as any}
                                        placeholder="e.g. Professional, empathetic, and concise. Use emojis sparingly."
                                        rows={3}
                                        className="w-full bg-secondary/30 border border-border rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-primary resize-none mt-2"
                                    />
                                    <p className="text-xs text-muted mt-1">The AI will adopt this persona when drafting suggested responses for you.</p>
                                </div>
                                <div className="pt-2">
                                    <button
                                        onClick={handleSaveConfig}
                                        disabled={isSavingConfig}
                                        className={`px-4 py-2 bg-secondary border border-border text-foreground transition-colors rounded-lg text-sm flex items-center gap-2 ${isSavingConfig ? "opacity-75 cursor-wait" : "hover:bg-card"}`}
                                    >
                                        {isSavingConfig ? (
                                            <>
                                                <span className="w-3 h-3 border-2 border-foreground/30 border-t-foreground rounded-full animate-spin" />
                                                Saving...
                                            </>
                                        ) : isSaved ? (
                                            <>
                                                <span className="text-green-500">✓</span>
                                                Saved!
                                            </>
                                        ) : "Save Configuration"}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Twitter Quota Display */}
                        {integrations.twitter && plan === "Pro" && (
                            <div className="glass-card p-6 border-primary/10">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                                    <span>🐦 Twitter Quota</span>
                                    <span className="text-xs px-2 py-1 bg-blue-500/20 text-blue-400 border border-blue-500/50 rounded">
                                        Pro Plan
                                    </span>
                                </h2>
                                <p className="text-sm text-muted mb-4">Your daily Twitter monitoring usage</p>

                                <div className="grid grid-cols-2 gap-4">
                                    {/* Searches Quota */}
                                    <div className="bg-secondary/20 rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-sm text-muted">Searches Today</span>
                                            <span className="text-xs text-muted">
                                                {twitterQuota.searches_today}/{twitterQuota.searches_limit}
                                            </span>
                                        </div>
                                        <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
                                            <div
                                                className={`h-full transition-all ${twitterQuota.searches_today >= twitterQuota.searches_limit ? 'bg-red-500' : 'bg-blue-500'}`}
                                                style={{ width: `${(twitterQuota.searches_today / twitterQuota.searches_limit) * 100}%` }}
                                            />
                                        </div>
                                        <p className="text-xs text-muted mt-2">
                                            {twitterQuota.searches_limit - twitterQuota.searches_today} searches remaining
                                        </p>
                                    </div>

                                    {/* Tweets Quota */}
                                    <div className="bg-secondary/20 rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-sm text-muted">Tweets Analyzed</span>
                                            <span className="text-xs text-muted">
                                                {twitterQuota.tweets_today}/{twitterQuota.tweets_limit}
                                            </span>
                                        </div>
                                        <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
                                            <div
                                                className={`h-full transition-all ${twitterQuota.tweets_today >= twitterQuota.tweets_limit ? 'bg-red-500' : 'bg-green-500'}`}
                                                style={{ width: `${(twitterQuota.tweets_today / twitterQuota.tweets_limit) * 100}%` }}
                                            />
                                        </div>
                                        <p className="text-xs text-muted mt-2">
                                            {twitterQuota.tweets_limit - twitterQuota.tweets_today} tweets remaining
                                        </p>
                                    </div>
                                </div>

                                <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                                    <p className="text-xs text-blue-400">
                                        ℹ️ Quota resets daily at midnight. Last reset: {twitterQuota.last_reset || 'N/A'}
                                    </p>
                                </div>
                            </div>
                        )}

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
                                            <p className={`text-xs ${config.subreddits ? "text-green-400" : "text-muted"}`}>
                                                {config.subreddits ? "Active (Scraping)" : "Inactive"}
                                            </p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => {
                                            document.getElementById('monitoring-config')?.scrollIntoView({ behavior: 'smooth' });
                                        }}
                                        className="text-xs text-muted hover:text-foreground"
                                    >
                                        Configure Sources
                                    </button>
                                </div>

                                {/* TikTok */}
                                <div className="flex items-center justify-between p-4 bg-secondary/20 rounded-lg opacity-75">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-black flex items-center justify-center font-bold text-white text-xs">T</div>
                                        <div>
                                            <p className="font-medium">TikTok</p>
                                            <p className="text-xs text-muted">Coming Soon</p>
                                        </div>
                                    </div>
                                    <button disabled className="px-3 py-1 bg-secondary/50 border border-border/50 text-muted rounded text-xs cursor-not-allowed">Coming Soon</button>
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
                                <div className="flex items-center justify-between p-4 bg-secondary/20 rounded-lg opacity-75">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-gradient-to-tr from-yellow-400 via-red-500 to-purple-500 flex items-center justify-center font-bold text-white text-xs">I</div>
                                        <div>
                                            <p className="font-medium">Instagram</p>
                                            <p className="text-xs text-muted">Coming Soon</p>
                                        </div>
                                    </div>
                                    <button disabled className="px-3 py-1 bg-secondary/50 border border-border/50 text-muted rounded text-xs cursor-not-allowed">Coming Soon</button>
                                </div>

                                {/* Facebook */}
                                <div className="flex items-center justify-between p-4 bg-secondary/20 rounded-lg opacity-75">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center font-bold text-white text-xs">F</div>
                                        <div>
                                            <p className="font-medium">Facebook</p>
                                            <p className="text-xs text-muted">Coming Soon</p>
                                        </div>
                                    </div>
                                    <button disabled className="px-3 py-1 bg-secondary/50 border border-border/50 text-muted rounded text-xs cursor-not-allowed">Coming Soon</button>
                                </div>

                                {/* Jira (Up sell) */}
                                <div className="flex items-center justify-between p-4 bg-secondary/20 rounded-lg opacity-75">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-blue-500 flex items-center justify-center font-bold text-white text-xs">J</div>
                                        <div>
                                            <p className="font-medium">Jira</p>
                                            <p className="text-xs text-muted">Coming Soon</p>
                                        </div>
                                    </div>
                                    <button disabled className="px-3 py-1 bg-secondary/50 border border-border/50 text-muted rounded text-xs cursor-not-allowed">Coming Soon</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main >

            {/* Payment Modal */}
            {
                showPaymentModal && (
                    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-background border-2 border-primary/20 rounded-2xl w-full max-w-3xl h-[700px] relative shadow-2xl shadow-primary/10">
                            {/* Modal Header */}
                            <div className="flex items-center justify-between p-6 border-b border-border">
                                <div>
                                    <h2 className="text-xl font-bold">Complete Your Payment</h2>
                                    <p className="text-sm text-muted mt-1">Secure payment powered by PesaPal</p>
                                </div>
                                <button
                                    onClick={() => setShowPaymentModal(false)}
                                    className="w-10 h-10 rounded-full hover:bg-secondary flex items-center justify-center transition-colors text-muted hover:text-foreground"
                                    title="Close"
                                >
                                    <span className="text-2xl">×</span>
                                </button>
                            </div>

                            {/* iFrame Container */}
                            <div className="h-[calc(100%-80px)]">
                                <iframe
                                    src={paymentUrl}
                                    className="w-full h-full"
                                    title="PesaPal Payment"
                                    allow="payment"
                                />
                            </div>
                        </div>
                    </div>
                )
            }
        </div >
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
