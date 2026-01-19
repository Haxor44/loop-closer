"use client";

export default function Waitlist() {
    return (
        <section className="py-24 px-6 relative overflow-hidden">
            <div className="absolute inset-0 bg-primary/5 -skew-y-3 transform origin-left" />
            <div className="relative z-10 max-w-4xl mx-auto glass-card p-12 text-center border-primary/20 bg-primary/10">
                <h2 className="text-3xl md:text-5xl font-bold mb-4">
                    Ready to <span className="gradient-text">Close the Loop?</span>
                </h2>
                <p className="text-xl text-muted mb-10 max-w-2xl mx-auto">
                    Start monitoring your brand in seconds. No credit card required for the free tier.
                </p>

                <a
                    href="/auth/signin"
                    className="inline-block px-12 py-5 bg-primary hover:bg-primary-hover text-white font-bold text-lg rounded-xl transition-all duration-300 transform hover:scale-105 shadow-xl shadow-primary/30"
                >
                    Get Started Now
                </a>
            </div>
        </section>
    );
}
