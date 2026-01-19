"use client";

export default function Hero() {
    return (
        <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
            {/* Background Gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-[#0f172a] via-[#1e1b4b] to-[#0f172a]" />

            {/* Floating Orbs */}
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-pulse" />
            <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent/20 rounded-full blur-3xl animate-pulse delay-1000" />

            <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
                {/* Badge */}
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary border border-border mb-8">
                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                    <span className="text-sm text-muted">Powered by AI Agents</span>
                </div>

                {/* Main Headline */}
                <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
                    Close the <span className="gradient-text">Feedback Loop</span>
                    <br />Automatically
                </h1>

                {/* Subheadline */}
                <p className="text-xl md:text-2xl text-muted max-w-3xl mx-auto mb-10">
                    Turn social media complaints into resolved tickets.
                    Notify your customers when their issues are fixed — without lifting a finger.
                </p>

                {/* CTA Buttons */}
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <a
                        href="/auth/signin"
                        className="px-8 py-4 bg-primary hover:bg-primary-hover text-white font-semibold rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg shadow-primary/25"
                    >
                        Get Started
                    </a>
                    <a
                        href="#features"
                        className="px-8 py-4 bg-secondary hover:bg-card text-foreground font-semibold rounded-xl border border-border transition-all duration-300"
                    >
                        Explore Features
                    </a>
                </div>

                {/* Social Proof */}
                <div className="mt-16 flex items-center justify-center gap-8 text-muted">
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold text-foreground">10K+</span>
                        <span className="text-sm">Tickets Closed</span>
                    </div>
                    <div className="w-px h-8 bg-border" />
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold text-foreground">500+</span>
                        <span className="text-sm">Happy Teams</span>
                    </div>
                    <div className="w-px h-8 bg-border" />
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold text-foreground">24/7</span>
                        <span className="text-sm">AI Monitoring</span>
                    </div>
                </div>
            </div>
        </section>
    );
}
