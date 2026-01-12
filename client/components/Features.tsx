"use client";

const features = [
    {
        icon: "🔍",
        title: "Multi-Platform Scraping",
        description: "Automatically ingests mentions from Twitter, Reddit, Facebook, and Instagram in real-time.",
    },
    {
        icon: "🧠",
        title: "AI-Powered Classification",
        description: "Uses advanced AI to classify posts as Bugs, Feature Requests, or Noise with high accuracy.",
    },
    {
        icon: "🎫",
        title: "Auto Ticket Creation",
        description: "Creates tickets in your preferred system (Jira, Linear, or our built-in tracker) automatically.",
    },
    {
        icon: "🔔",
        title: "Proactive Notifications",
        description: "Notifies customers on social media when their reported issue is resolved.",
    },
    {
        icon: "🔗",
        title: "n8n Integration",
        description: "Seamlessly connects to n8n for custom workflows, Slack alerts, and more.",
    },
    {
        icon: "🚀",
        title: "Zero Config Deployment",
        description: "Get started in minutes with our hosted solution or self-host with Docker.",
    },
];

export default function Features() {
    return (
        <section id="features" className="py-24 px-6">
            <div className="max-w-6xl mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-4xl md:text-5xl font-bold mb-4">
                        Everything You Need to <span className="gradient-text">Close the Loop</span>
                    </h2>
                    <p className="text-xl text-muted max-w-2xl mx-auto">
                        From social listening to customer delight, all on autopilot.
                    </p>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {features.map((feature, index) => (
                        <div
                            key={index}
                            className="glass-card p-6 hover:border-primary/50 transition-all duration-300 group"
                        >
                            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">
                                {feature.icon}
                            </div>
                            <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                            <p className="text-muted">{feature.description}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
