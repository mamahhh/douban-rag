"use client";

import { useState } from "react";
import { signInWithEmailAndPassword, GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState("");
    const router = useRouter();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(""); // Clear previous errors
        try {
            await signInWithEmailAndPassword(auth, email, password);
            router.push("/dashboard");
        } catch (err: any) {
            setError(err.message);
        }
    };

    const handleGoogleLogin = async () => {
        setError(""); // Clear previous errors
        try {
            const provider = new GoogleAuthProvider();
            await signInWithPopup(auth, provider);
            router.push("/dashboard");
        } catch (err: any) {
            setError(err.message);
        }
    };

    return (
        <div className="bg-background-light dark:bg-background-dark font-display text-white min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/20 rounded-full blur-[120px] mix-blend-screen opacity-40"></div>
                <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-blue-500/10 rounded-full blur-[100px] mix-blend-screen opacity-30"></div>
                <div className="absolute inset-0 bg-grid-pattern z-0"></div>
            </div>
            <div className="relative z-10 w-full max-w-[400px] bg-[#121613] rounded-2xl shadow-2xl border border-[#404f43] overflow-hidden flex flex-col max-h-[90vh]">
                <div className="flex items-center justify-between p-6 pb-2">
                    <h2 className="text-2xl font-bold tracking-tight text-white">Sign In</h2>
                    <Link href="/" className="text-[#a2b3a5] hover:text-white transition-colors p-2 -mr-2 rounded-full hover:bg-white/5">
                        <span className="material-symbols-outlined text-2xl">close</span>
                    </Link>
                </div>
                <div className="overflow-y-auto px-6 py-2">
                    <p className="text-[#a2b3a5] text-sm mb-6">Welcome back to the Douban RAG knowledge base.</p>

                    {error && (
                        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500 text-sm text-center">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleLogin} className="space-y-5">
                        <div className="space-y-2">
                            <label className="text-white text-sm font-medium block" htmlFor="email">Email Address</label>
                            <div className="relative group">
                                <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[#a2b3a5] group-focus-within:text-primary transition-colors text-xl">mail</span>
                                <input
                                    className="w-full h-12 pl-12 pr-4 bg-[#1e241f] border border-[#404f43] rounded-xl text-white placeholder:text-[#5a6b5d] focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-all text-base"
                                    id="email"
                                    placeholder="name@example.com"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between items-center">
                                <label className="text-white text-sm font-medium block" htmlFor="password">Password</label>
                                <a className="text-xs text-primary hover:text-[#5acc6e] font-medium transition-colors" href="#">Forgot Password?</a>
                            </div>
                            <div className="relative group flex items-center">
                                <span className="material-symbols-outlined absolute left-4 text-[#a2b3a5] group-focus-within:text-primary transition-colors text-xl">lock</span>
                                <input
                                    className="w-full h-12 pl-12 pr-12 bg-[#1e241f] border border-[#404f43] rounded-xl text-white placeholder:text-[#5a6b5d] focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none transition-all text-base"
                                    id="password"
                                    placeholder="Enter your password"
                                    type={showPassword ? "text" : "password"}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                />
                                <button
                                    className="absolute right-0 top-0 h-full px-4 text-[#a2b3a5] hover:text-white flex items-center justify-center focus:outline-none"
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                >
                                    <span className="material-symbols-outlined text-xl">
                                        {showPassword ? "visibility_off" : "visibility"}
                                    </span>
                                </button>
                            </div>
                        </div>
                        <button
                            className="w-full h-12 bg-primary hover:bg-[#3aa84d] text-[#121613] font-bold rounded-xl text-base transition-transform active:scale-[0.98] flex items-center justify-center shadow-lg shadow-primary/20 mt-2"
                            type="submit"
                        >
                            Sign In
                        </button>
                    </form>
                    <div className="relative flex py-6 items-center">
                        <div className="flex-grow border-t border-[#404f43]"></div>
                        <span className="flex-shrink-0 mx-4 text-[#a2b3a5] text-xs font-medium uppercase tracking-wider">Or</span>
                        <div className="flex-grow border-t border-[#404f43]"></div>
                    </div>
                    <div className="space-y-3 pb-2">
                        <button
                            onClick={handleGoogleLogin}
                            type="button"
                            className="w-full h-12 bg-white text-gray-900 font-semibold rounded-xl text-base transition-transform active:scale-[0.98] flex items-center justify-center gap-3 hover:bg-gray-100"
                        >
                            <svg className="w-5 h-5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"></path>
                                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"></path>
                                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"></path>
                                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"></path>
                            </svg>
                            Continue with Google
                        </button>
                    </div>
                </div>
                <div className="p-6 pt-2 text-center">
                    <p className="text-[#a2b3a5] text-sm">
                        Don't have an account?
                        <Link href="/auth/signup" className="text-primary font-semibold hover:text-[#5acc6e] transition-colors ml-1">Sign Up</Link>
                    </p>
                </div>
                <div className="w-full h-1 absolute bottom-1 left-0 flex justify-center pointer-events-none opacity-0 sm:opacity-0">
                </div>
            </div>
        </div>
    );
}
