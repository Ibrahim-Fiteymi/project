import { useEffect, useRef, useCallback, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
    ImageIcon,
    FileUp,
    Component as Figma,
    MonitorIcon,
    CircleUserRound,
    ArrowUpIcon,
    Paperclip,
    PlusIcon,
} from "lucide-react";

interface UseAutoResizeTextareaProps {
    minHeight: number;
    maxHeight?: number;
}

function useAutoResizeTextarea({
    minHeight,
    maxHeight,
}: UseAutoResizeTextareaProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const adjustHeight = useCallback(
        (reset?: boolean) => {
            const textarea = textareaRef.current;
            if (!textarea) return;

            if (reset) {
                textarea.style.height = `${minHeight}px`;
                return;
            }

            textarea.style.height = `${minHeight}px`;
            const newHeight = Math.max(
                minHeight,
                Math.min(
                    textarea.scrollHeight,
                    maxHeight ?? Number.POSITIVE_INFINITY
                )
            );
            textarea.style.height = `${newHeight}px`;
        },
        [minHeight, maxHeight]
    );

    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) textarea.style.height = `${minHeight}px`;
    }, [minHeight]);

    useEffect(() => {
        const handleResize = () => adjustHeight();
        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, [adjustHeight]);

    return { textareaRef, adjustHeight };
}

type ChatRole = "user" | "assistant";
interface ChatMessage {
    id: string;
    role: ChatRole;
    content: string;
}

const SUGGESTED_REPLIES: Record<string, string> = {
    hello: "Hi there! How can I help you ship today?",
    hi: "Hey — what are you building?",
};

function generateAssistantReply(prompt: string): string {
    const lower = prompt.trim().toLowerCase();
    for (const k of Object.keys(SUGGESTED_REPLIES)) {
        if (lower.startsWith(k)) return SUGGESTED_REPLIES[k];
    }
    if (lower.includes("nuclei") || lower.includes("cell")) {
        return "For nuclei segmentation, head to **New Analysis** in the sidebar — upload a microscopy image and the model will produce a mask + count.";
    }
    if (lower.endsWith("?")) {
        return `That's a great question. Here's a quick take on "${prompt.trim()}" — try breaking it into a smaller, concrete first step and we can iterate from there.`;
    }
    return `Got it — "${prompt.trim()}". I'd start by sketching the data flow, then wire up the smallest end-to-end slice before adding polish.`;
}

export function VercelV0Chat() {
    const [value, setValue] = useState("");
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isThinking, setIsThinking] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const { textareaRef, adjustHeight } = useAutoResizeTextarea({
        minHeight: 60,
        maxHeight: 200,
    });

    const hasStarted = messages.length > 0 || isThinking;

    useEffect(() => {
        const el = scrollRef.current;
        if (el) el.scrollTop = el.scrollHeight;
    }, [messages, isThinking]);

    const handleSubmit = useCallback(() => {
        const trimmed = value.trim();
        if (!trimmed || isThinking) return;

        const userMsg: ChatMessage = {
            id: `${Date.now()}-u`,
            role: "user",
            content: trimmed,
        };
        setMessages((m) => [...m, userMsg]);
        setValue("");
        adjustHeight(true);
        setIsThinking(true);

        const replyDelay = 700 + Math.random() * 600;
        setTimeout(() => {
            setMessages((m) => [
                ...m,
                {
                    id: `${Date.now()}-a`,
                    role: "assistant",
                    content: generateAssistantReply(trimmed),
                },
            ]);
            setIsThinking(false);
        }, replyDelay);
    }, [value, isThinking, adjustHeight]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const handleSuggestion = (label: string) => {
        setValue(label);
        textareaRef.current?.focus();
        adjustHeight();
    };

    return (
        <div className="flex flex-col items-center w-full max-w-4xl mx-auto p-4 space-y-6">
            <AnimatePresence initial={false}>
                {!hasStarted && (
                    <motion.h1
                        key="hero"
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -12 }}
                        transition={{ duration: 0.35, ease: "easeOut" }}
                        className="text-4xl font-bold text-black dark:text-white text-center"
                    >
                        What can I help you ship?
                    </motion.h1>
                )}
            </AnimatePresence>

            <AnimatePresence initial={false}>
                {hasStarted && (
                    <motion.div
                        key="messages"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                        className="w-full"
                    >
                        <div
                            ref={scrollRef}
                            className="w-full max-h-[55vh] overflow-y-auto space-y-3 pr-1"
                        >
                            <AnimatePresence initial={false}>
                                {messages.map((m) => (
                                    <motion.div
                                        key={m.id}
                                        layout
                                        initial={{ opacity: 0, y: 10, scale: 0.98 }}
                                        animate={{ opacity: 1, y: 0, scale: 1 }}
                                        transition={{
                                            duration: 0.25,
                                            ease: "easeOut",
                                        }}
                                        className={cn(
                                            "flex",
                                            m.role === "user"
                                                ? "justify-end"
                                                : "justify-start"
                                        )}
                                    >
                                        <div
                                            className={cn(
                                                "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap",
                                                m.role === "user"
                                                    ? "bg-white text-black"
                                                    : "bg-neutral-900 text-neutral-100 border border-neutral-800"
                                            )}
                                        >
                                            {m.content}
                                        </div>
                                    </motion.div>
                                ))}

                                {isThinking && (
                                    <motion.div
                                        key="typing"
                                        initial={{ opacity: 0, y: 6 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                        className="flex justify-start"
                                    >
                                        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl px-4 py-3 flex items-center gap-1.5">
                                            {[0, 1, 2].map((i) => (
                                                <motion.span
                                                    key={i}
                                                    className="w-1.5 h-1.5 rounded-full bg-neutral-400"
                                                    animate={{
                                                        y: [0, -3, 0],
                                                        opacity: [0.4, 1, 0.4],
                                                    }}
                                                    transition={{
                                                        duration: 0.9,
                                                        repeat: Infinity,
                                                        delay: i * 0.15,
                                                    }}
                                                />
                                            ))}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <motion.div
                layout
                transition={{ duration: 0.3, ease: "easeOut" }}
                className="w-full"
            >
                <div className="relative bg-neutral-900 rounded-xl border border-neutral-800 focus-within:border-neutral-700 transition-colors">
                    <div className="overflow-y-auto">
                        <Textarea
                            ref={textareaRef}
                            value={value}
                            onChange={(e) => {
                                setValue(e.target.value);
                                adjustHeight();
                            }}
                            onKeyDown={handleKeyDown}
                            placeholder={
                                hasStarted
                                    ? "Send a message..."
                                    : "Ask v0 a question..."
                            }
                            className={cn(
                                "w-full px-4 py-3",
                                "resize-none",
                                "bg-transparent",
                                "border-none",
                                "text-white text-sm",
                                "focus:outline-none",
                                "focus-visible:ring-0 focus-visible:ring-offset-0",
                                "placeholder:text-neutral-500 placeholder:text-sm",
                                "min-h-[60px]"
                            )}
                            style={{ overflow: "hidden" }}
                        />
                    </div>

                    <div className="flex items-center justify-between p-3">
                        <div className="flex items-center gap-2">
                            <motion.button
                                type="button"
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="group p-2 hover:bg-neutral-800 rounded-lg transition-colors flex items-center gap-1"
                            >
                                <Paperclip className="w-4 h-4 text-white" />
                                <span className="text-xs text-zinc-400 hidden group-hover:inline transition-opacity">
                                    Attach
                                </span>
                            </motion.button>
                        </div>
                        <div className="flex items-center gap-2">
                            <motion.button
                                type="button"
                                whileHover={{ scale: 1.04 }}
                                whileTap={{ scale: 0.96 }}
                                className="px-2 py-1 rounded-lg text-sm text-zinc-400 transition-colors border border-dashed border-zinc-700 hover:border-zinc-600 hover:bg-zinc-800 flex items-center justify-between gap-1"
                            >
                                <PlusIcon className="w-4 h-4" />
                                Project
                            </motion.button>
                            <motion.button
                                type="button"
                                onClick={handleSubmit}
                                disabled={!value.trim() || isThinking}
                                whileHover={
                                    value.trim() && !isThinking
                                        ? { scale: 1.06 }
                                        : undefined
                                }
                                whileTap={
                                    value.trim() && !isThinking
                                        ? { scale: 0.92 }
                                        : undefined
                                }
                                className={cn(
                                    "px-1.5 py-1.5 rounded-lg text-sm transition-colors border border-zinc-700 flex items-center justify-center gap-1 disabled:cursor-not-allowed",
                                    value.trim() && !isThinking
                                        ? "bg-white text-black border-white hover:bg-neutral-200"
                                        : "text-zinc-400 hover:bg-zinc-800"
                                )}
                                aria-label="Send message"
                            >
                                <ArrowUpIcon
                                    className={cn(
                                        "w-4 h-4",
                                        value.trim() && !isThinking
                                            ? "text-black"
                                            : "text-zinc-400"
                                    )}
                                />
                                <span className="sr-only">Send</span>
                            </motion.button>
                        </div>
                    </div>
                </div>

                <AnimatePresence initial={false}>
                    {!hasStarted && (
                        <motion.div
                            key="suggestions"
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -8 }}
                            transition={{ duration: 0.3, delay: 0.05 }}
                            className="flex flex-wrap items-center justify-center gap-3 mt-4"
                        >
                            {ACTIONS.map((a, i) => (
                                <ActionButton
                                    key={a.label}
                                    icon={a.icon}
                                    label={a.label}
                                    delay={0.08 * i}
                                    onClick={() => handleSuggestion(a.label)}
                                />
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
}

const ACTIONS: { icon: React.ReactNode; label: string }[] = [
    { icon: <ImageIcon className="w-4 h-4" />, label: "Clone a Screenshot" },
    { icon: <Figma className="w-4 h-4" />, label: "Import from Figma" },
    { icon: <FileUp className="w-4 h-4" />, label: "Upload a Project" },
    { icon: <MonitorIcon className="w-4 h-4" />, label: "Landing Page" },
    { icon: <CircleUserRound className="w-4 h-4" />, label: "Sign Up Form" },
];

interface ActionButtonProps {
    icon: React.ReactNode;
    label: string;
    delay?: number;
    onClick?: () => void;
}

function ActionButton({ icon, label, delay = 0, onClick }: ActionButtonProps) {
    return (
        <motion.button
            type="button"
            onClick={onClick}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay, ease: "easeOut" }}
            whileHover={{ scale: 1.04, y: -2 }}
            whileTap={{ scale: 0.96 }}
            className="flex items-center gap-2 px-4 py-2 bg-neutral-900 hover:bg-neutral-800 rounded-full border border-neutral-800 text-neutral-400 hover:text-white transition-colors"
        >
            {icon}
            <span className="text-xs">{label}</span>
        </motion.button>
    );
}
