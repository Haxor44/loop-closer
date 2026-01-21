import { useState } from "react";

interface ReplyModalProps {
    isOpen: boolean;
    onClose: () => void;
    ticketContent: string;
    ticketId: string;
    brandVoice?: string;
}

export default function ReplyModal({ isOpen, onClose, ticketContent, ticketId, brandVoice }: ReplyModalProps) {
    const [reply, setReply] = useState("");
    const [loading, setLoading] = useState(false);
    const [context, setContext] = useState("");
    const [generatedOnce, setGeneratedOnce] = useState(false);

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
                setGeneratedOnce(true);
            }
        } catch (error) {
            console.error("Error generating reply:", error);
        } finally {
            setLoading(false);
        }
    };

    // Auto-generate on open if brandVoice is available and haven't generated yet
    if (!generatedOnce && !loading && !reply && brandVoice) {
        // Using a timeout to avoid strict mode double-invoke issues in dev
        setTimeout(() => generateReply(brandVoice), 100);
        setGeneratedOnce(true);
    }

    const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    const handleSend = async () => {
        if (!reply) return;
        setLoading(true);
        setStatus(null);

        try {
            // Using "Twitter" hardcoded for now, or derive from ticketSource if available
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/tickets/${ticketId}/reply`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    content: reply,
                    platform: "Twitter"
                })
            });

            if (res.ok) {
                setStatus({ type: 'success', message: 'Reply posted to Twitter! 🐦' });
                // Short delay to let user see the success message
                setTimeout(() => {
                    onClose();
                }, 1500);
            } else {
                const err = await res.json();
                setStatus({ type: 'error', message: err.detail || 'Failed to post reply' });
            }
        } catch (error) {
            console.error("Failed to send reply:", error);
            setStatus({ type: 'error', message: 'Network error. Please try again.' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div
            className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-opacity"
            onClick={onClose}
        >
            <div
                className="bg-background border-l border-border shadow-2xl w-full max-w-xl h-full flex flex-col relative animate-in slide-in-from-right duration-300 ease-out"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="p-6 border-b border-border flex justify-between items-center shrink-0 bg-secondary/10">
                    <div>
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            <span className="text-primary">Reply to Customer</span>
                            <span className="text-sm px-2 py-0.5 bg-primary/10 text-primary rounded-full font-normal">Twitter</span>
                        </h2>
                        <p className="text-xs text-muted mt-1 flex items-center gap-1.5 overflow-hidden">
                            <span className="shrink-0 font-medium">Ticket:</span>
                            <span className="truncate italic">"{ticketContent}"</span>
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-secondary rounded-full transition-all text-muted hover:text-foreground border border-transparent hover:border-border"
                        title="Close Drawer"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>

                {/* Main Content */}
                <div className="p-6 space-y-8 overflow-y-auto flex-1 min-h-0 custom-scrollbar">
                    {/* Tone Selection Section */}
                    <div className="space-y-3">
                        <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                            <span className="w-1 h-1 bg-primary rounded-full"></span>
                            {brandVoice ? "Target Brand Voice" : "Response Tone & Vibe"}
                        </label>
                        <div className="flex flex-wrap gap-2">
                            {["Professional", "Empathetic", "Direct", "Noir", "Vibrant", "Soft"].map((tone) => (
                                <button
                                    key={tone}
                                    onClick={() => generateReply(tone)}
                                    disabled={loading}
                                    className={`px-4 py-2 rounded-xl text-sm transition-all border ${brandVoice === tone
                                        ? 'bg-primary/20 border-primary text-primary font-medium'
                                        : 'bg-secondary/40 border-border text-muted-hover:bg-secondary/60 hover:border-primary/50'
                                        } disabled:opacity-50`}
                                >
                                    {tone}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Context Input Section */}
                    <div className="space-y-3">
                        <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                            <span className="w-1 h-1 bg-primary rounded-full"></span>
                            Additional Context
                        </label>
                        <div className="relative group">
                            <input
                                type="text"
                                className="w-full px-4 py-3 bg-secondary/20 border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all placeholder:text-muted/30"
                                placeholder="Specific instructions? (e.g. mention refund policy)"
                                value={context}
                                onChange={(e) => setContext(e.target.value)}
                            />
                        </div>
                    </div>

                    {/* AI Editor Section */}
                    <div className="space-y-3 flex-1 flex flex-col min-h-0">
                        <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                            <span className="w-1 h-1 bg-primary rounded-full"></span>
                            Response Draft
                        </label>
                        <div className="relative flex-1 min-h-0">
                            <textarea
                                value={reply}
                                onChange={(e) => setReply(e.target.value)}
                                className="w-full h-full min-h-[300px] bg-secondary/10 border border-border rounded-2xl p-6 text-sm leading-relaxed focus:ring-2 focus:ring-primary/20 focus:border-primary/30 transition-all resize-none font-sans"
                                placeholder={brandVoice ? "Synthesizing response with your brand voice..." : "Select a tone above to generate a draft..."}
                            />
                            {loading && (
                                <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/40 backdrop-blur-[2px] rounded-2xl border border-primary/20 shadow-inner">
                                    <div className="w-8 h-8 border-3 border-primary/30 border-t-primary rounded-full animate-spin mb-3" />
                                    <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary animate-pulse">
                                        Generating...
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Feedback Toast (Inline) */}
                {status && (
                    <div className={`mx-6 mb-4 px-4 py-3 rounded-xl text-sm font-medium border animate-in slide-in-from-bottom-2 duration-300 ${status.type === 'success'
                        ? 'text-green-500 bg-green-500/5 border-green-500/20'
                        : 'text-red-500 bg-red-500/5 border-red-500/20'
                        }`}>
                        <div className="flex items-center gap-2">
                            {status.type === 'success' ? '✅' : '❌'}
                            {status.message}
                        </div>
                    </div>
                )}

                {/* Sticky Footer */}
                <div className="p-6 border-t border-border bg-secondary/20 shrink-0">
                    <div className="flex items-center justify-between gap-4">
                        <button
                            onClick={onClose}
                            className="px-6 py-2.5 text-sm font-medium text-muted hover:text-foreground transition-all rounded-xl hover:bg-secondary"
                        >
                            Discard
                        </button>
                        <div className="flex flex-col items-end gap-2">
                            <button
                                onClick={handleSend}
                                disabled={!reply || loading}
                                className="px-8 py-3 bg-black text-white rounded-xl text-sm font-bold hover:bg-neutral-800 shadow-xl shadow-neutral-900/20 transform transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-3"
                            >
                                {loading ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        Posting...
                                    </>
                                ) : (
                                    <>
                                        <span>Post to X</span>
                                        <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current" aria-hidden="true">
                                            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"></path>
                                        </svg>
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                    <div className="mt-3 flex items-center justify-end gap-2">
                        <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                        <span className="text-[10px] text-muted font-medium uppercase tracking-tight">Connected via X Cloud API</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
