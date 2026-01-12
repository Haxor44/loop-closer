"use client";

export default function Footer() {
    return (
        <footer className="py-12 px-6 border-t border-border">
            <div className="max-w-6xl mx-auto">
                <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="flex items-center gap-2">
                        <span className="text-2xl">🔄</span>
                        <span className="text-xl font-bold">The Loop Closer</span>
                    </div>

                    <div className="flex gap-8 text-muted text-sm">
                        <a href="#features" className="hover:text-foreground transition-colors">Features</a>
                        <a href="#pricing" className="hover:text-foreground transition-colors">Pricing</a>
                        <a href="https://github.com" className="hover:text-foreground transition-colors">GitHub</a>
                        <a href="/docs" className="hover:text-foreground transition-colors">Docs</a>
                    </div>

                    <p className="text-muted text-sm">
                        © 2026 The Loop Closer. All rights reserved.
                    </p>
                </div>
            </div>
        </footer>
    );
}
