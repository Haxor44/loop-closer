"use client";

const plans = [
    {
        name: "Free",
        tagline: "For Starters",
        price: "$0",
        period: "/month",
        description: "Perfect for testing the waters.",
        features: [
            "1 Global Keyword",
            "1 Subreddit",
            "Manual Ticket Management",
            "Basic Dashboard",
            "Community Support",
        ],
        cta: "Get Started",
        highlighted: false,
        href: "/auth/signin"
    },
    {
        name: "Pro",
        tagline: "For Builders",
        price: "$8",
        period: "/month",
        description: "Unlock full monitoring power.",
        features: [
            "Unlimited Keywords",
            "Unlimited Subreddits",
            "AI Sarcasm Detection",
            "Urgency Analysis",
            "Priority Support",
            "Remove Branding"
        ],
        cta: "Go Pro",
        highlighted: true,
        href: "/auth/signin"
    },
    {
        name: "Teams",
        tagline: "For Scale",
        price: "Coming Soon",
        period: "",
        description: "Enterprise integrations.",
        features: [
            "Jira Sync (Coming Soon)",
            "Linear Integration",
            "Slack Alerts",
            "SSO Authentication",
            "Dedicated Manager",
        ],
        cta: "Join Waitlist",
        highlighted: false,
        href: "#"
    },
];

export default function Pricing() {
    return (
        <section id="pricing" className="py-24 px-6 bg-secondary/50">
            <div className="max-w-6xl mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-4xl md:text-5xl font-bold mb-4">
                        Simple, <span className="gradient-text">Transparent</span> Pricing
                    </h2>
                    <p className="text-xl text-muted max-w-2xl mx-auto">
                        Choose the path that fits your workflow. No hidden fees.
                    </p>
                </div>

                <div className="grid md:grid-cols-3 gap-8">
                    {plans.map((plan, index) => (
                        <div
                            key={index}
                            className={`relative rounded-2xl p-8 transition-all duration-300 hover:scale-105 ${plan.highlighted
                                ? "bg-gradient-to-b from-primary/20 to-transparent border-2 border-primary shadow-xl shadow-primary/20"
                                : "glass-card"
                                }`}
                        >
                            {plan.highlighted && (
                                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-primary text-white text-sm font-semibold rounded-full">
                                    Most Popular
                                </div>
                            )}

                            <div className="mb-6">
                                <p className="text-accent text-sm font-medium mb-1">{plan.tagline}</p>
                                <h3 className="text-2xl font-bold">{plan.name}</h3>
                                <p className="text-muted text-sm mt-2">{plan.description}</p>
                            </div>

                            <div className="mb-6">
                                <span className="text-5xl font-bold">{plan.price}</span>
                                <span className="text-muted">{plan.period}</span>
                            </div>

                            <ul className="space-y-3 mb-8">
                                {plan.features.map((feature, i) => (
                                    <li key={i} className="flex items-center gap-3 text-sm">
                                        <svg className="w-5 h-5 text-accent flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                        </svg>
                                        <span>{feature}</span>
                                    </li>
                                ))}
                            </ul>

                            <a
                                href={plan.href}
                                className={`w-full py-3 px-6 rounded-xl font-semibold text-center transition-all duration-300 ${plan.highlighted
                                    ? "bg-primary hover:bg-primary-hover text-white shadow-lg shadow-primary/25"
                                    : "bg-secondary hover:bg-card border border-border"
                                    }`}
                            >
                                {plan.cta}
                            </a>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
