"use client";

import StatusBadge from "./StatusBadge";
import { useState } from "react";
import ReplyModal from "./ReplyModal";

interface Ticket {
    id: string;
    summary: string;
    status: "OPEN" | "IN_PROGRESS" | "DONE";
    type?: "BUG" | "FEATURE" | "QUESTION";
    urgency?: "high" | "medium" | "low";
    linked_users: string[];
    created_at: number;
}

const UrgencyBadge = ({ urgency }: { urgency?: string }) => {
    const colors = {
        high: "bg-red-500/20 text-red-400 border-red-500/30",
        medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
        low: "bg-green-500/20 text-green-400 border-green-500/30"
    };

    const level = urgency || "low";

    return (
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wide ${colors[level as keyof typeof colors] || colors.low}`}>
            {level === "high" ? "🔥 " : level === "medium" ? "⚡ " : "✓ "}{level}
        </span>
    );
};

export default function TicketTable({ tickets, refresh, brandVoice }: { tickets: Ticket[], refresh: () => void, brandVoice?: string }) {
    const [selectedTicket, setSelectedTicket] = useState<{ id: string, content: string } | null>(null);

    const handleStatusUpdate = async (id: string, currentStatus: string) => {
        const nextStatus = currentStatus === "OPEN" ? "IN_PROGRESS" : currentStatus === "IN_PROGRESS" ? "DONE" : "OPEN";

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/tickets/${id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: nextStatus })
            });

            if (res.ok) {
                refresh();
            }
        } catch (error) {
            console.error("Failed to update status:", error);
        }
    };

    if (tickets.length === 0) {
        return <div className="p-12 text-center text-muted">No social tickets found yet.</div>;
    }

    // Sort by urgency (high first) then by created_at
    const sortedTickets = [...tickets].sort((a, b) => {
        const urgencyOrder = { high: 0, medium: 1, low: 2 };
        const aUrgency = urgencyOrder[a.urgency as keyof typeof urgencyOrder] ?? 2;
        const bUrgency = urgencyOrder[b.urgency as keyof typeof urgencyOrder] ?? 2;
        if (aUrgency !== bUrgency) return aUrgency - bUrgency;
        return b.created_at - a.created_at;
    });

    return (
        <div className="overflow-x-auto">
            <table className="w-full text-left">
                <thead>
                    <tr className="border-b border-border bg-secondary/30 text-sm font-medium">
                        <th className="px-6 py-4">Ticket ID</th>
                        <th className="px-6 py-4">Summary</th>
                        <th className="px-6 py-4">Type</th>
                        <th className="px-6 py-4">Urgency</th>
                        <th className="px-6 py-4">Platform/User</th>
                        <th className="px-6 py-4">Status</th>
                        <th className="px-6 py-4 text-right">Actions</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-border">
                    {sortedTickets.map((ticket) => (
                        <tr key={ticket.id} className={`hover:bg-secondary/20 transition-colors group ${ticket.urgency === 'high' ? 'bg-red-500/5' : ''}`}>
                            <td className="px-6 py-4 font-mono text-xs text-primary">{ticket.id}</td>
                            <td className="px-6 py-4 max-w-md">
                                <p className="font-medium whitespace-normal break-words">{ticket.summary}</p>
                                <p className="text-xs text-muted">Created {new Date(ticket.created_at * 1000).toLocaleDateString()}</p>
                            </td>
                            <td className="px-6 py-4">
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wide
                                    ${ticket.type === 'BUG' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                        ticket.type === 'FEATURE' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                                            'bg-gray-500/10 text-gray-400 border-gray-500/20'}`}>
                                    {ticket.type || "QUESTION"}
                                </span>
                            </td>
                            <td className="px-6 py-4">
                                <UrgencyBadge urgency={ticket.urgency} />
                            </td>
                            <td className="px-6 py-4">
                                <span className="text-sm">{ticket.linked_users[0] || "Anonymous"}</span>
                            </td>
                            <td className="px-6 py-4">
                                <StatusBadge status={ticket.status} />
                            </td>
                            <td className="px-6 py-4 text-right">
                                <button
                                    onClick={() => handleStatusUpdate(ticket.id, ticket.status)}
                                    className="px-3 py-1.5 bg-secondary hover:bg-primary/20 hover:text-primary border border-border rounded-md text-xs transition-all"
                                >
                                    Cycle Status
                                </button>
                                <button
                                    onClick={() => setSelectedTicket({ id: ticket.id, content: ticket.summary })}
                                    className="ml-2 px-3 py-1.5 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 rounded-md text-xs transition-all"
                                >
                                    Reply
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {selectedTicket && (
                <ReplyModal
                    isOpen={!!selectedTicket}
                    onClose={() => setSelectedTicket(null)}
                    ticketId={selectedTicket.id}
                    ticketContent={selectedTicket.content}
                    brandVoice={brandVoice}
                />
            )}
        </div>
    );
}
