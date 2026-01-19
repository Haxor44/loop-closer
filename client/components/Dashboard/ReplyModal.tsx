import { useState } from "react";

interface ReplyModalProps {
    isOpen: boolean;
    onClose: () => void;
    ticketContent: string;
    ticketId: string;
}

export default function ReplyModal({ isOpen, onClose, ticketContent, ticketId }: ReplyModalProps) {
    const [reply, setReply] = useState("");
    const [loading, setLoading] = useState(false);
    const [context, setContext] = useState("");

    if (!isOpen) return null;

    const generateReply = async (tone: string) => {
        setLoading(true);
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/generate-reply`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content: ticketContent, tone, context })
            });
            const data = await res.json();
            if (data.reply) {
                setReply(data.reply);
            }
        } catch (error) {
            console.error("Error generating reply:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSend = () => {
        // Mock send functionality
        alert(`Reply sent for ticket ${ticketId}:\n${reply}`);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-background border border-border rounded-xl shadow-2xl w-full max-w-lg overflow-hidden">
                <div className="p-6 border-b border-border">
                    <h3 className="text-lg font-bold">Generate Reply</h3>
                    <p className="text-sm text-muted mt-1 truncate">Replying to: {ticketContent}</p>
                </div>

                <div className="p-6 space-y-4">
                    {/* Quick Prompts */}
                    <div>
                        <label className="text-xs font-semibold uppercase text-muted mb-2 block">Quick Prompts / Vibe</label>
                        <div className="flex flex-wrap gap-2">
                            {["Professional", "Empathic", "Direct", "Noir", "Vibrant", "Soft"].map((tone) => (
                                <button
                                    key={tone}
                                    onClick={() => generateReply(tone)}
                                    disabled={loading}
                                    className="px-3 py-1.5 bg-secondary hover:bg-primary/20 hover:text-primary rounded-full text-xs transition-colors border border-border"
                                >
                                    {tone}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Context Input */}
                    <div>
                        <label className="text-xs font-semibold uppercase text-muted mb-2 block">Additional Context (Optional)</label>
                        <input
                            type="text"
                            className="w-full px-3 py-2 bg-secondary/50 border border-border rounded-lg text-sm focus:outline-none focus:border-primary/50"
                            placeholder="e.g., Mention the 20% discount code..."
                            value={context}
                            onChange={(e) => setContext(e.target.value)}
                        />
                    </div>

                    {/* Reply Textarea */}
                    <div className="relative">
                        <textarea
                            value={reply}
                            onChange={(e) => setReply(e.target.value)}
                            className="w-full h-32 bg-secondary/30 border border-border rounded-lg p-3 text-sm focus:ring-1 focus:ring-primary focus:border-primary resize-none"
                            placeholder="AI generated reply will appear here..."
                        />
                        {loading && (
                            <div className="absolute inset-0 flex items-center justify-center bg-background/50 backdrop-blur-sm rounded-lg">
                                <div className="text-xs font-bold animate-pulse text-primary">Generating...</div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="p-4 bg-secondary/30 flex justify-end gap-3 border-t border-border">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm text-muted hover:text-foreground transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSend}
                        disabled={!reply}
                        className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        Send Reply
                    </button>
                </div>
            </div>
        </div>
    );
}
