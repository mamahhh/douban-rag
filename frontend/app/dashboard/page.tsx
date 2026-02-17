"use client";

import { useEffect, useState, useRef } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter, useSearchParams } from "next/navigation";
import { signOut } from "firebase/auth";
import { auth } from "@/lib/firebase";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Upload, Send, LogOut, FileText, Music, Film, Book, Gamepad2, Mic2, Database, Trash2 } from "lucide-react";

// Types
interface Message {
    role: "user" | "assistant";
    content: string;
}

interface UploadResult {
    documents_processed: number;
    media_types: Record<string, number>;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Dashboard() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const searchParams = useSearchParams();
    const isDemo = searchParams.get("demo") === "true";

    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isUploading, setIsUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState("");
    const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
    const [chatLoading, setChatLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Redirect if not logged in (unless demo)
    useEffect(() => {
        if (!loading && !user && !isDemo) {
            router.push("/auth/login");
        }
    }, [user, loading, isDemo, router]);

    // Load chat history and data status on mount
    useEffect(() => {
        const loadUserData = async () => {
            try {
                const token = user ? await user.getIdToken() : (isDemo ? "demo-token" : "");
                if (!token) return;

                // Load chat history
                const historyRes = await fetch(`${BACKEND_URL}/api/chat/history`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                if (historyRes.ok) {
                    const data = await historyRes.json();
                    if (data.messages && data.messages.length > 0) {
                        setMessages(data.messages.map((m: any) => ({ role: m.role, content: m.content })));
                    }
                }

                // Load upload/data status
                const statusRes = await fetch(`${BACKEND_URL}/api/data/status`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                if (statusRes.ok) {
                    const data = await statusRes.json();
                    if (data.status) {
                        setUploadResult({
                            documents_processed: data.status.documents_processed,
                            media_types: data.status.media_types,
                        });
                    }
                }
            } catch (err) {
                console.error("Failed to load user data:", err);
            }
        };
        if (!loading && (user || isDemo)) {
            loadUserData();
        }
    }, [user, loading, isDemo]);

    // Scroll to bottom of chat
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleLoadDemoData = async () => {
        setIsUploading(true);
        setUploadStatus("Loading demo data...");
        try {
            const response = await fetch("/api/demo", { method: "POST" });
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            setUploadStatus("Demo data loaded successfully!");
            setTimeout(() => setUploadStatus(""), 3000);
        } catch (error: any) {
            console.error(error);
            setUploadStatus(`Error: ${error.message}`);
        } finally {
            setIsUploading(false);
        }
    };

    const handleLogout = async () => {
        if (auth) await signOut(auth);
        router.push("/");
    };

    const [progress, setProgress] = useState(0);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files?.[0]) return;

        if (isDemo) {
            setUploadStatus("Demo mode: File upload disabled");
            return;
        }

        const file = e.target.files[0];
        const formData = new FormData();
        formData.append("file", file);

        setIsUploading(true);
        setUploadStatus("Starting upload...");
        setProgress(0);

        try {
            const token = user ? await user.getIdToken() : "";

            // Use fetch instead of axios to handle streaming response
            const response = await fetch(`${BACKEND_URL}/api/upload/stream`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                body: formData,
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Upload failed: ${response.status} ${errorText}`);
            }

            if (!response.body) {
                throw new Error("No response body");
            }

            // Read the stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split("\n\n");

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const data = JSON.parse(line.substring(6));

                            if (data.stage === "error") {
                                throw new Error(data.message);
                            }

                            if (data.progress !== undefined) {
                                setProgress(data.progress);
                            }

                            if (data.message) {
                                setUploadStatus(data.message);
                            }

                            if (data.stage === "complete") {
                                setUploadStatus("Processing complete!");
                                setProgress(100);
                                if (data.documents_processed && data.media_types) {
                                    setUploadResult({
                                        documents_processed: data.documents_processed,
                                        media_types: data.media_types
                                    });
                                }
                                setTimeout(() => {
                                    setUploadStatus("");
                                    setProgress(0);
                                }, 3000);
                            }
                        } catch (e) {
                            // Ignore parse errors for partial chunks
                            console.log("Error parsing chunk", e);
                        }
                    }
                }
            }

        } catch (error: any) {
            console.error(error);
            setUploadStatus(`Error: ${error.message}`);
            setProgress(0);
        } finally {
            setIsUploading(false);
        }
    };

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        const newMessage: Message = { role: "user", content: input };
        setMessages((prev) => [...prev, newMessage]);
        setInput("");
        setChatLoading(true);

        try {
            const token = user ? await user.getIdToken() : (isDemo ? "demo-token" : "");

            const response = await fetch(`${BACKEND_URL}/api/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ message: newMessage.content }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const botReply = data.response;
            setMessages((prev) => [...prev, { role: "assistant", content: botReply }]);
        } catch (error: any) {
            console.error(error);
            setMessages((prev) => [...prev, { role: "assistant", content: "Error: Could not connect to backend." }]);
        } finally {
            setChatLoading(false);
        }
    };

    if (loading) return <div className="min-h-screen flex items-center justify-center bg-background-dark text-white">Loading...</div>;

    return (
        <div className="flex h-screen bg-background-light dark:bg-background-dark overflow-hidden">
            {/* Sidebar */}
            <div className="w-64 bg-white dark:bg-[#102218] border-r border-gray-200 dark:border-white/5 flex flex-col p-4">
                <div className="flex items-center gap-2 mb-8 px-2">
                    <span className="material-symbols-outlined text-primary text-2xl">smart_toy</span>
                    <h1 className="font-display font-bold text-xl text-slate-800 dark:text-white">Douban <span className="text-primary">RAG</span></h1>
                </div>

                <div className="flex-1">
                    <p className="text-xs font-semibold text-slate-500 dark:text-gray-500 uppercase tracking-wider mb-2 px-2">Data Source</p>

                    {uploadResult ? (
                        <div className="space-y-3 px-2">
                            <div className="p-3 bg-emerald-50 dark:bg-emerald-900/10 rounded-lg border border-emerald-100 dark:border-emerald-900/20">
                                <div className="flex items-center gap-2 mb-2 text-emerald-700 dark:text-emerald-400">
                                    <span className="material-symbols-outlined text-xl">check_circle</span>
                                    <h3 className="text-sm font-bold">Upload Complete</h3>
                                </div>
                                <p className="text-xs text-slate-600 dark:text-gray-300 mb-2">
                                    Processed <span className="font-bold">{uploadResult.documents_processed}</span> items.
                                </p>
                                <div className="space-y-1 mb-3">
                                    {Object.entries(uploadResult.media_types).map(([type, count]) => (
                                        <div key={type} className="flex justify-between text-[10px] text-slate-500 dark:text-gray-400 uppercase tracking-wider">
                                            <span>{type}</span>
                                            <span className="font-mono">{count}</span>
                                        </div>
                                    ))}
                                </div>
                                <button
                                    onClick={() => {
                                        setUploadResult(null);
                                        setUploadStatus("");
                                        setProgress(0);
                                    }}
                                    className="w-full py-1.5 bg-white dark:bg-white/10 hover:bg-gray-50 dark:hover:bg-white/20 border border-emerald-200 dark:border-white/10 rounded text-xs font-semibold text-emerald-700 dark:text-emerald-300 transition-colors"
                                >
                                    Upload Another
                                </button>
                            </div>
                        </div>
                    ) : isDemo ? (
                        <div className="space-y-3 px-2">
                            <div className="p-3 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-100 dark:border-blue-900/20">
                                <p className="text-xs text-blue-600 dark:text-blue-400 mb-2">
                                    <span className="font-bold">Demo Mode:</span> Uploads are disabled. You can load sample data to test the system.
                                </p>
                                <button
                                    onClick={handleLoadDemoData}
                                    disabled={isUploading}
                                    className="w-full flex items-center justify-center gap-2 py-2 bg-primary text-background-dark rounded-md text-sm font-bold hover:opacity-90 transition-opacity disabled:opacity-50"
                                >
                                    {isUploading ? (
                                        <span className="w-4 h-4 border-2 border-background-dark border-t-transparent rounded-full animate-spin"></span>
                                    ) : (
                                        <Database size={16} />
                                    )}
                                    {isUploading ? "Loading..." : "Load Demo Data"}
                                </button>
                            </div>
                        </div>
                    ) : (
                        <label className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors ${isUploading ? 'bg-primary/10 text-primary' : 'hover:bg-gray-100 dark:hover:bg-white/5 text-slate-700 dark:text-gray-300'}`}>
                            <Upload size={18} />
                            <span className="text-sm font-medium">Upload File</span>
                            <input type="file" onChange={handleFileUpload} className="hidden" accept=".csv,.xlsx" disabled={isUploading} />
                        </label>
                    )}

                    {/* Progress Bar */}
                    {(isUploading || progress > 0) && (
                        <div className="mt-3 px-2">
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mb-1 overflow-hidden">
                                <div
                                    className="bg-primary h-1.5 rounded-full transition-all duration-300 ease-out"
                                    style={{ width: `${progress}%` }}
                                ></div>
                            </div>
                            <div className="flex justify-between text-[10px] text-slate-400 dark:text-gray-500">
                                <span>{progress}%</span>
                            </div>
                        </div>
                    )}

                    {uploadStatus && <p className={`text-xs mt-1 px-3 ${uploadStatus.startsWith("Error") ? "text-red-500" : "text-primary"} truncate`}>{uploadStatus}</p>}
                </div>

                <div className="border-t border-gray-200 dark:border-white/5 pt-4">
                    <div className="flex items-center gap-3 px-2 mb-4">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-emerald-400 flex items-center justify-center text-background-dark font-bold text-xs">
                            {user?.email?.[0].toUpperCase() || "D"}
                        </div>
                        <div className="flex-1 overflow-hidden">
                            <p className="text-sm font-medium text-slate-800 dark:text-white truncate">{user?.email || "Demo User"}</p>
                            <p className="text-xs text-slate-500 dark:text-gray-500 truncate">{isDemo ? "Demo Mode" : "Free Plan"}</p>
                        </div>
                    </div>
                    {messages.length > 0 && (
                        <button
                            onClick={async () => {
                                try {
                                    const token = user ? await user.getIdToken() : (isDemo ? "demo-token" : "");
                                    await fetch(`${BACKEND_URL}/api/chat/history`, {
                                        method: "DELETE",
                                        headers: { Authorization: `Bearer ${token}` },
                                    });
                                    setMessages([]);
                                } catch (err) {
                                    console.error("Failed to clear history:", err);
                                }
                            }}
                            className="flex items-center gap-3 px-3 py-2 w-full rounded-lg text-slate-500 dark:text-gray-400 hover:bg-amber-50 dark:hover:bg-amber-900/10 hover:text-amber-600 transition-colors mb-1"
                        >
                            <Trash2 size={18} />
                            <span className="text-sm font-medium">Clear History</span>
                        </button>
                    )}
                    <button onClick={handleLogout} className="flex items-center gap-3 px-3 py-2 w-full rounded-lg text-slate-500 dark:text-gray-400 hover:bg-red-50 dark:hover:bg-red-900/10 hover:text-red-600 transition-colors">
                        <LogOut size={18} />
                        <span className="text-sm font-medium">Log Out</span>
                    </button>
                </div>
            </div>

            <div className="flex-1 flex flex-col bg-gray-50 dark:bg-black/20">
                {/* Chat Area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth">
                    {messages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-center p-8 opacity-50">
                            <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                                <span className="material-symbols-outlined text-primary text-3xl">chat_bubble_outline</span>
                            </div>
                            <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">How can I help you today?</h3>
                            <p className="text-slate-500 dark:text-gray-400 max-w-sm">Ask me about your movies, books, or music history. I can analyze trends and find specific items.</p>
                        </div>
                    ) : (
                        messages.map((msg, idx) => (
                            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`max-w-[80%] rounded-2xl px-5 py-3.5 shadow-sm ${msg.role === 'user'
                                    ? 'bg-primary text-background-dark rounded-br-none'
                                    : 'bg-white dark:bg-[#1c3a29] text-slate-800 dark:text-gray-100 rounded-bl-none border border-gray-200 dark:border-white/5'
                                    }`}>
                                    {msg.role === 'assistant' ? (
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            components={{
                                                p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                                                strong: ({ children }) => <strong className="font-bold">{children}</strong>,
                                                em: ({ children }) => <em className="italic">{children}</em>,
                                                h1: ({ children }) => <h1 className="text-xl font-bold mb-2 mt-3">{children}</h1>,
                                                h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-3">{children}</h2>,
                                                h3: ({ children }) => <h3 className="text-base font-bold mb-1.5 mt-2">{children}</h3>,
                                                ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                                                ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                                                li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                                                a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary underline hover:opacity-80">{children}</a>,
                                                code: ({ className, children, ...props }) => {
                                                    const isInline = !className;
                                                    return isInline
                                                        ? <code className="bg-black/10 dark:bg-white/10 px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>
                                                        : <code className={`block bg-black/10 dark:bg-black/30 p-3 rounded-lg text-sm font-mono overflow-x-auto my-2 ${className || ''}`} {...props}>{children}</code>;
                                                },
                                                pre: ({ children }) => <pre className="my-2">{children}</pre>,
                                                blockquote: ({ children }) => <blockquote className="border-l-4 border-primary/40 pl-3 my-2 italic opacity-90">{children}</blockquote>,
                                                table: ({ children }) => <div className="overflow-x-auto my-2"><table className="min-w-full text-sm border-collapse">{children}</table></div>,
                                                thead: ({ children }) => <thead className="bg-black/5 dark:bg-white/5">{children}</thead>,
                                                th: ({ children }) => <th className="border border-gray-300 dark:border-white/10 px-3 py-1.5 text-left font-semibold">{children}</th>,
                                                td: ({ children }) => <td className="border border-gray-300 dark:border-white/10 px-3 py-1.5">{children}</td>,
                                                hr: () => <hr className="my-3 border-gray-300 dark:border-white/10" />,
                                            }}
                                        >
                                            {msg.content}
                                        </ReactMarkdown>
                                    ) : (
                                        msg.content
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                    {chatLoading && (
                        <div className="flex justify-start">
                            <div className="bg-white dark:bg-[#1c3a29] px-5 py-4 rounded-2xl rounded-bl-none border border-gray-200 dark:border-white/5 flex gap-1">
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-4 bg-white dark:bg-[#102218] border-t border-gray-200 dark:border-white/5">
                    <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto relative flex items-center gap-2 bg-gray-50 dark:bg-black/20 p-2 rounded-xl border border-gray-200 dark:border-white/10 focus-within:ring-2 focus-within:ring-primary/50 transition-all">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type your message..."
                            className="flex-1 bg-transparent border-none focus:ring-0 text-slate-800 dark:text-white placeholder-slate-400 px-2"
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || chatLoading}
                            className="p-2 bg-primary text-background-dark rounded-lg hover:bg-emerald-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <Send size={18} />
                        </button>
                    </form>
                    <p className="text-center text-[10px] text-slate-400 dark:text-gray-600 mt-2">
                        Douban RAG can make mistakes. Verify important information.
                    </p>
                </div>
            </div>
        </div >
    );
}
