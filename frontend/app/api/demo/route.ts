
import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import axios from "axios";

// Force Node.js runtime to access filesystem
export const runtime = "nodejs";

export async function POST() {
    try {
        // Locate the demo file relative to the project root
        // frontend is the CWD for the Next.js server
        // Data is in ../data/demo.xlsx
        const demoFilePath = path.join(process.cwd(), "../data/demo.xlsx");

        if (!fs.existsSync(demoFilePath)) {
            return NextResponse.json(
                { error: "Demo file not found on server" },
                { status: 404 }
            );
        }

        const fileBuffer = fs.readFileSync(demoFilePath);
        const blob = new Blob([fileBuffer], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });

        const formData = new FormData();
        formData.append("file", blob, "demo.xlsx");

        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

        // Upload to backend
        // Note: We use 'demo-token' as the authorization, matching the Streamlit logic
        const response = await fetch(`${backendUrl}/api/upload/stream`, {
            method: "POST",
            headers: {
                Authorization: "Bearer demo-token",
            },
            body: formData,
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Backend error: ${response.status} ${errorText}`);
        }

        // Pass through the response (or a success message)
        // The backend returns a stream, but fetch here might buffer it unless we explicitly stream.
        // For simplicity, we'll confirm success.
        return NextResponse.json({ success: true, message: "Demo data loaded successfully" });

    } catch (error: any) {
        console.error("Demo upload error:", error);
        return NextResponse.json(
            { error: error.message || "Internal Server Error" },
            { status: 500 }
        );
    }
}
