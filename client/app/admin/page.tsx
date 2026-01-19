"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Dashboard/Sidebar";

export default function AdminPage() {
    const { data: session, status } = useSession();
    const router = useRouter();
    const [users, setUsers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    // Hardcoded Admin Check for MVP
    const ADMIN_EMAIL = "evolmalek04@gmail.com";

    useEffect(() => {
        if (status === "unauthenticated") {
            router.push("/api/auth/signin");
        } else if (session) {
            // Strict Admin Check
            if (session.user?.email !== ADMIN_EMAIL) {
                router.push("/dashboard");
                return;
            }
            fetchUsers();
        }
    }, [session, status]);

    const fetchUsers = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users`);
            const data = await res.json();
            setUsers(data.users || []);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const calculateRevenue = () => {
        let total = 0;
        users.forEach(u => {
            if (u.plan === 'Pro') total += 29;
            if (u.plan === 'Teams') total += 99; // Teams plan placeholder
        });
        return total;
    };

    const [selectedUser, setSelectedUser] = useState<any>(null);

    const handlePlanChange = async (email: string, newPlan: string) => {
        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users/${email}/plan`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ plan: newPlan })
            });
            // Refund/Update local state
            setUsers(users.map(u => u.email === email ? { ...u, plan: newPlan } : u));
            setSelectedUser(null);
        } catch (e) {
            alert("Failed to update plan");
        }
    };

    if (status === "loading" || loading) return <div className="p-8 text-white">Loading Admin Panel...</div>;

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto p-8 pt-12">
                <div className="max-w-5xl mx-auto">
                    <h1 className="text-3xl font-bold mb-8 flex items-center gap-3">
                        🛡️ Admin Console
                        <span className="text-xs bg-red-500/20 text-red-500 px-2 py-1 rounded border border-red-500/50">Restricted</span>
                    </h1>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <div className="glass-card p-6 border-primary/10">
                            <p className="text-sm text-muted">Total Users</p>
                            <p className="text-3xl font-bold">{users.length}</p>
                        </div>
                        <div className="glass-card p-6 border-primary/10">
                            <p className="text-sm text-muted">Pro Subscribers</p>
                            <p className="text-3xl font-bold text-blue-400">{users.filter(u => u.plan === 'Pro').length}</p>
                        </div>
                        <div className="glass-card p-6 border-primary/10">
                            <p className="text-sm text-muted">Total Revenue (Est)</p>
                            <p className="text-3xl font-bold text-green-400">${calculateRevenue()}</p>
                        </div>
                    </div>

                    <div className="glass-card border-primary/10 overflow-hidden">
                        <table className="w-full text-left">
                            <thead className="bg-secondary/50 text-xs uppercase text-muted">
                                <tr>
                                    <th className="px-6 py-4">User</th>
                                    <th className="px-6 py-4">Email</th>
                                    <th className="px-6 py-4">Plan</th>
                                    <th className="px-6 py-4">Joined</th>
                                    <th className="px-6 py-4">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border/50">
                                {users.map((user, i) => (
                                    <tr key={i} className="hover:bg-secondary/30 transition-colors">
                                        <td className="px-6 py-4 font-medium">{user.name}</td>
                                        <td className="px-6 py-4 text-muted">{user.email}</td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded text-xs font-bold border ${user.plan === 'Pro' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                                                'bg-gray-500/10 text-gray-400 border-gray-500/20'
                                                }`}>
                                                {user.plan.toUpperCase()}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-muted text-sm">{new Date(user.joined_at * 1000).toLocaleDateString()}</td>
                                        <td className="px-6 py-4">
                                            <button
                                                onClick={() => setSelectedUser(user)}
                                                className="text-xs text-primary hover:text-primary/80">
                                                Manage
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                                {users.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-8 text-center text-muted">No users found.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Manage User Modal */}
                {selectedUser && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                        <div className="bg-[#111] border border-white/10 p-6 rounded-xl w-full max-w-md shadow-2xl">
                            <h2 className="text-xl font-bold mb-4">Manage User: {selectedUser.name}</h2>
                            <p className="text-sm text-muted mb-6">Change subscription plan manually.</p>

                            <div className="space-y-3">
                                <button
                                    onClick={() => handlePlanChange(selectedUser.email, 'Free')}
                                    className="w-full p-3 text-left rounded bg-secondary/20 hover:bg-secondary/40 border border-white/5 flex justify-between">
                                    <span>Free Plan</span>
                                    {selectedUser.plan === 'Free' && <span>✅</span>}
                                </button>
                                <button
                                    onClick={() => handlePlanChange(selectedUser.email, 'Pro')}
                                    className="w-full p-3 text-left rounded bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 text-blue-400 flex justify-between">
                                    <span>Pro Plan ($29)</span>
                                    {selectedUser.plan === 'Pro' && <span>✅</span>}
                                </button>
                                <button
                                    onClick={() => handlePlanChange(selectedUser.email, 'Teams')}
                                    className="w-full p-3 text-left rounded bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/20 text-purple-400 flex justify-between">
                                    <span>Teams Plan (Coming Soon)</span>
                                    {selectedUser.plan === 'Teams' && <span>✅</span>}
                                </button>
                            </div>

                            <button
                                onClick={() => setSelectedUser(null)}
                                className="mt-6 w-full py-2 text-sm text-muted hover:text-white">
                                Cancel
                            </button>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
