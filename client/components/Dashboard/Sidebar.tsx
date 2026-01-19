import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";
import { useEffect, useState } from "react";

export default function Sidebar() {
    const pathname = usePathname();
    const { data: session } = useSession();
    const [userName, setUserName] = useState("");
    const [isMobileOpen, setIsMobileOpen] = useState(false);

    useEffect(() => {
        if (session?.user?.email) {
            fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/sync`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: session.user.email, name: session.user.name })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.user?.name) {
                        setUserName(data.user.name);
                    } else {
                        setUserName(session.user?.name || "Guest");
                    }
                })
                .catch(() => setUserName(session.user?.name || "Guest"));
        }
    }, [session]);

    const displayName = userName || session?.user?.name || "Guest";

    return (
        <>
            {/* Mobile Toggle Button */}
            <button
                className="md:hidden fixed top-4 left-4 z-50 p-2 bg-secondary rounded-lg border border-border"
                onClick={() => setIsMobileOpen(!isMobileOpen)}
            >
                {isMobileOpen ? "✖" : "☰"}
            </button>

            {/* Backdrop */}
            {isMobileOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 md:hidden"
                    onClick={() => setIsMobileOpen(false)}
                />
            )}

            <aside className={`fixed md:static inset-y-0 left-0 z-50 w-64 border-r border-border bg-background/95 backdrop-blur-xl flex flex-col h-full transition-transform duration-300 md:translate-x-0 ${isMobileOpen ? "translate-x-0" : "-translate-x-full"
                }`}>
                <div className="p-8 mt-8 md:mt-0">
                    <Link href="/" className="text-xl font-bold flex items-center gap-2">
                        🔄 <span className="gradient-text">Loop Closer</span>
                    </Link>
                </div>

                <nav className="flex-1 px-4 py-4 space-y-1">
                    {[
                        { name: "Tickets", icon: "🎟️", href: "/dashboard" },
                        { name: "Settings", icon: "⚙️", href: "/dashboard/settings" },
                        // Only show Admin link to Admin
                        ...(session?.user?.email === "evolmalek04@gmail.com" ? [{ name: "Admin", icon: "🛡️", href: "/admin" }] : [])
                    ].map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${isActive
                                    ? "bg-primary text-white shadow-lg shadow-primary/25"
                                    : "text-muted hover:bg-secondary hover:text-foreground"
                                    }`}
                            >
                                <span>{item.icon}</span>
                                <span className="font-medium">{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-border">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-accent flex items-center justify-center font-bold text-white text-xs">
                            {displayName[0] || "U"}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm truncate">{displayName}</p>
                            <p className="text-xs text-muted truncate">{session?.user?.email || "Not signed in"}</p>
                        </div>
                        {session && (
                            <button
                                onClick={() => signOut({ callbackUrl: "/" })}
                                className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 px-2 py-1 rounded hover:bg-red-500/10 transition-colors"
                                title="Sign Out"
                            >
                                🚪 <span>Logout</span>
                            </button>
                        )}
                    </div>
                </div>
            </aside>
        </>
    );
}
