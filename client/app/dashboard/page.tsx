"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Sidebar from "../../components/Dashboard/Sidebar";
import TicketTable from "../../components/Dashboard/TicketTable";

export default function DashboardPage() {
    const [tickets, setTickets] = useState<any[]>([]);
    const [stats, setStats] = useState({ total: 0, open: 0, done: 0 });
    const [loading, setLoading] = useState(true);
    const { data: session, status } = useSession();
    const router = useRouter();

    useEffect(() => {
        if (status === "unauthenticated") {
            router.push("/");
        }
    }, [status, router]);

    const fetchData = async () => {
        if (!session?.user?.email) return;

        try {
            const [ticketsRes, statsRes] = await Promise.all([
                fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/tickets?email=${session.user.email}`),
                fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/stats?email=${session.user.email}`)
            ]);

            const ticketsData = await ticketsRes.json();
            const statsData = await statsRes.json();

            setTickets(ticketsData);
            setStats(statsData);
        } catch (error) {
            console.error("Error fetching dashboard data:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (session?.user?.email) {
            fetchData();
        }
    }, [session]);

    if (status === "loading") {
        return <div className="flex h-screen items-center justify-center">Loading...</div>;
    }

    if (status === "unauthenticated") {
        return null; // Will redirect
    }

    return (
        <div className="flex flex-col md:flex-row h-screen bg-background text-foreground overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto p-8 pt-12">
                <div className="max-w-6xl mx-auto">
                    <div className="mb-8 flex justify-between items-end">
                        <div>
                            <h1 className="text-3xl font-bold mb-2">Social Tickets</h1>
                            <p className="text-muted">Monitor and resolve social media feedback in real-time.</p>
                        </div>
                        <button
                            onClick={fetchData}
                            className="px-4 py-2 bg-secondary hover:bg-card border border-border rounded-lg text-sm transition-colors"
                        >
                            Refresh Data
                        </button>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                        {[
                            { label: "Total Tickets", value: stats.total, color: "text-primary" },
                            { label: "Active/Open", value: stats.open, color: "text-accent" },
                            { label: "Resolved", value: stats.done, color: "text-green-400" },
                        ].map((stat, i) => (
                            <div key={i} className="glass-card p-6 border-primary/10">
                                <p className="text-sm text-muted mb-1">{stat.label}</p>
                                <p className={`text-4xl font-bold ${stat.color}`}>{stat.value}</p>
                            </div>
                        ))}
                    </div>

                    {/* Tickets Table */}
                    <div className="glass-card overflow-hidden border-primary/10">
                        {loading ? (
                            <div className="p-12 text-center text-muted">Loading tickets...</div>
                        ) : (
                            <TicketTable tickets={tickets} refresh={fetchData} />
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
