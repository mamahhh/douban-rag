import Link from "next/link";

export default function Home() {
    return (
        <div
            className="relative flex w-full flex-col justify-between overflow-hidden bg-background-light dark:bg-background-dark"
            style={{ minHeight: "max(884px, 100dvh)" }}
        >
            {/* Background Effects */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/20 rounded-full blur-[120px] mix-blend-screen opacity-40"></div>
                <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-blue-500/10 rounded-full blur-[100px] mix-blend-screen opacity-30"></div>
                <div className="absolute inset-0 bg-grid-pattern z-0"></div>
            </div>

            {/* Hero Section */}
            <div className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 pt-12 pb-6">
                <div className="flex flex-col items-center gap-6 w-full max-w-sm animate-fade-in-up">
                    {/* Logo */}
                    <div className="relative group">
                        <div className="absolute -inset-1 bg-gradient-to-tr from-primary to-emerald-400 rounded-full blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
                        <div className="relative w-32 h-32 md:w-40 md:h-40 bg-gradient-to-br from-[#1c3a29] to-[#102218] border border-white/10 rounded-[2.5rem] shadow-2xl flex flex-col items-center justify-center overflow-hidden">
                            <div className="relative z-10 flex items-center justify-center">
                                <span
                                    className="font-display font-extrabold text-white text-7xl md:text-8xl tracking-tighter leading-none"
                                    style={{ textShadow: "0 4px 20px rgba(19, 236, 109, 0.4)" }}
                                >
                                    豆
                                </span>
                                <div className="absolute -top-1 -right-4 bg-primary text-background-dark rounded-full p-1.5 shadow-lg flex items-center justify-center animate-bounce duration-[3000ms]">
                                    <span
                                        className="material-symbols-outlined text-lg font-bold"
                                        style={{ fontSize: "20px" }}
                                    >
                                        smart_toy
                                    </span>
                                </div>
                            </div>
                            <div className="absolute bottom-0 w-full h-1/2 bg-gradient-to-t from-primary/10 to-transparent"></div>
                            <div className="absolute -bottom-4 -right-4 w-20 h-20 rounded-full border border-primary/20"></div>
                            <div className="absolute -bottom-2 -left-2 w-16 h-16 rounded-full border border-primary/10"></div>
                        </div>
                    </div>

                    {/* Text */}
                    <div className="text-center space-y-2 mt-4">
                        <h1 className="text-slate-900 dark:text-white tracking-tight text-4xl md:text-5xl font-extrabold leading-tight">
                            Douban <span className="text-primary">RAG</span>
                        </h1>
                        <p className="text-slate-500 dark:text-gray-400 text-base md:text-lg font-medium leading-relaxed max-w-[280px] mx-auto">
                            Your intelligent guide to movies, books, and music.
                        </p>
                    </div>
                </div>
            </div>

            {/* Buttons */}
            <div className="relative z-10 w-full px-6 py-8 pb-12 bg-gradient-to-t from-background-light via-background-light to-transparent dark:from-background-dark dark:via-background-dark dark:to-transparent">
                <div className="max-w-md mx-auto flex flex-col gap-4">
                    <Link
                        href="/dashboard?demo=true"
                        className="group relative flex w-full cursor-pointer items-center justify-center overflow-hidden rounded-xl h-14 px-6 bg-primary text-background-dark shadow-[0_0_20px_-5px_rgba(19,236,109,0.4)] hover:shadow-[0_0_25px_-5px_rgba(19,236,109,0.6)] transition-all duration-300 transform hover:-translate-y-0.5 no-underline"
                    >
                        <span className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></span>
                        <span className="relative text-lg font-bold leading-normal tracking-wide flex items-center gap-2">
                            Try Demo
                            <span className="material-symbols-outlined text-[20px] font-bold">
                                arrow_forward
                            </span>
                        </span>
                    </Link>

                    <div className="flex items-center justify-between gap-4 mt-2">
                        <Link
                            href="/auth/signup"
                            className="flex-1 flex cursor-pointer items-center justify-center rounded-lg h-12 px-4 bg-slate-200/50 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-300 dark:border-white/10 text-slate-700 dark:text-white text-sm font-bold tracking-wide transition-colors no-underline"
                        >
                            Sign Up
                        </Link>
                        <Link
                            href="/auth/login"
                            className="flex-1 flex cursor-pointer items-center justify-center rounded-lg h-12 px-4 bg-transparent hover:bg-slate-200/50 dark:hover:bg-white/5 text-slate-600 dark:text-gray-300 hover:text-slate-900 dark:hover:text-white text-sm font-bold tracking-wide transition-colors no-underline"
                        >
                            Sign In
                        </Link>
                    </div>
                    <p className="text-center text-xs text-slate-400 dark:text-gray-500 mt-4">
                        By continuing, you agree to our Terms & Privacy Policy.
                    </p>
                </div>
            </div>
        </div>
    );
}
