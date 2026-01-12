import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";

export default function Sidebar() {
    const pathname = usePathname();
    const { data: session } = useSession();

    return (
        <aside className="w-64 border-r border-border bg-secondary/30 backdrop-blur-xl flex flex-col h-full">
            <div className="p-8">
                <Link href="/" className="text-xl font-bold flex items-center gap-2">
                    🔄 <span className="gradient-text">Loop Closer</span>
                </Link>
            </div>

            <nav className="flex-1 px-4 py-4 space-y-1">
                {[
                    { name: "Tickets", icon: "🎟️", href: "/dashboard" },
                    { name: "Settings", icon: "⚙️", href: "/dashboard/settings" },
                    // FOR DEMO: Show Admin link to everyone
                    { name: "Admin", icon: "🛡️", href: "/admin" }
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
                        {session?.user?.name?.[0] || "U"}
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{session?.user?.name || "Guest"}</p>
                        <p className="text-xs text-muted truncate">{session?.user?.email || "Not signed in"}</p>
                    </div>
                    {session && (
                        <button
                            onClick={() => signOut({ callbackUrl: "/auth/signin" })}
                            className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 px-2 py-1 rounded hover:bg-red-500/10 transition-colors"
                            title="Sign Out"
                        >
                            🚪 <span>Logout</span>
                        </button>
                    )}
                </div>
            </div>
        </aside>
    );
}
