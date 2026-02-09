import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";

const plusJakartaSans = Plus_Jakarta_Sans({
    subsets: ["latin"],
    variable: "--font-plus-jakarta-sans",
});

export const metadata: Metadata = {
    title: "Douban RAG System",
    description: "Your intelligent guide to movies, books, and music.",
};


export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en" className="dark">
            <head>
                <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
                <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
                <script
                    dangerouslySetInnerHTML={{
                        __html: `
                            tailwind.config = {
                                darkMode: "class",
                                theme: {
                                    extend: {
                                        colors: {
                                            "primary": "#13ec6d",
                                            "background-light": "#f6f8f7",
                                            "background-dark": "#102218",
                                        },
                                        fontFamily: {
                                            "display": ["var(--font-plus-jakarta-sans)", "sans-serif"]
                                        },
                                        animation: {
                                            "fade-in-up": "fadeInUp 0.5s ease-out",
                                            bounce: "bounce 3s infinite",
                                        },
                                        keyframes: {
                                            fadeInUp: {
                                                "0%": { opacity: "0", transform: "translateY(10px)" },
                                                "100%": { opacity: "1", transform: "translateY(0)" },
                                            },
                                        },
                                    },
                                },
                            }
                        `,
                    }}
                />
            </head>
            <body className={`${plusJakartaSans.variable} font-display bg-background-light dark:bg-background-dark text-slate-900 dark:text-white`}>
                <AuthProvider>
                    {children}
                </AuthProvider>
            </body>
        </html>
    );
}
