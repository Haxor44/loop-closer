"use client";

import { useState } from "react";

export default function Waitlist() {
    const [email, setEmail] = useState("");
    const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
    const [message, setMessage] = useState("");

    const handleShare = () => {
        const text = encodeURIComponent("I just joined the waitlist for The Loop Closer! 🔄 Closing the customer feedback loop on autopilot. Join me: https://theloopcloser.com"); // Placeholder URL
        window.open(`https://twitter.com/intent/tweet?text=${text}`, "_blank");
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setStatus("loading");

        try {
            const res = await fetch("/api/waitlist", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email }),
            });

            if (res.ok) {
                setStatus("success");
                setMessage("You're on the list! We'll be in touch soon.");
                setEmail("");
            } else {
                const data = await res.json();
                setStatus("error");
                setMessage(data.error || "Something went wrong. Please try again.");
            }
        } catch (err) {
            setStatus("error");
            setMessage("Failed to join. Please check your connection.");
        }
    };

    return (
        <section id="waitlist" className="py-24 px-6 relative overflow-hidden">
            <div className="absolute inset-0 bg-primary/5 -skew-y-3 transform origin-left" />
            <div className="relative z-10 max-w-4xl mx-auto glass-card p-12 text-center border-primary/20 bg-primary/10">
                {status === "success" ? (
                    <div className="animate-in fade-in zoom-in duration-500">
                        <div className="text-6xl mb-6">🎉</div>
                        <h2 className="text-3xl md:text-5xl font-bold mb-4">
                            You're <span className="gradient-text">On the List!</span>
                        </h2>
                        <p className="text-xl text-muted mb-8 max-w-2xl mx-auto">
                            Want to move up the queue? Share The Loop Closer with your network and we'll bump you to the front of the line.
                        </p>
                        <button
                            onClick={handleShare}
                            className="inline-flex items-center gap-2 px-8 py-4 bg-[#000000] hover:bg-[#1a1a1a] text-white font-semibold rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg shadow-white/5 border border-white/10"
                        >
                            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                            </svg>
                            Share on X
                        </button>
                        <button
                            onClick={() => setStatus("idle")}
                            className="block mt-6 text-sm text-muted hover:text-foreground transition-colors mx-auto"
                        >
                            Back to form
                        </button>
                    </div>
                ) : (
                    <>
                        <h2 className="text-3xl md:text-5xl font-bold mb-4">
                            Ready to <span className="gradient-text">Join the Future</span> of Support?
                        </h2>
                        <p className="text-xl text-muted mb-10 max-w-2xl mx-auto">
                            Be the first to know when we launch the Cloud version. No spam, just updates on our progress.
                        </p>

                        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4 max-w-lg mx-auto">
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="Enter your email"
                                required
                                className="flex-1 px-6 py-4 rounded-xl bg-secondary border border-border focus:outline-none focus:border-primary transition-colors text-foreground"
                            />
                            <button
                                type="submit"
                                disabled={status === "loading"}
                                className="px-8 py-4 bg-primary hover:bg-primary-hover text-white font-semibold rounded-xl transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:scale-100 shadow-lg shadow-primary/25"
                            >
                                {status === "loading" ? "Joining..." : "Join the Waitlist"}
                            </button>
                        </form>

                        {message && status === "error" && (
                            <div className="mt-6 text-sm text-red-400">
                                {message}
                            </div>
                        )}
                    </>
                )}
            </div>
        </section>
    );
}
