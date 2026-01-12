export default function StatusBadge({ status }: { status: "OPEN" | "IN_PROGRESS" | "DONE" }) {
    const styles: Record<string, string> = {
        OPEN: "bg-accent/10 text-accent border-accent/20",
        IN_PROGRESS: "bg-primary/10 text-primary border-primary/20",
        DONE: "bg-green-400/10 text-green-400 border-green-400/20",
    };

    return (
        <span className={`px-2 py-1 rounded-full text-[10px] font-bold border uppercase tracking-wider ${styles[status]}`}>
            {status.replace("_", " ")}
        </span>
    );
}
