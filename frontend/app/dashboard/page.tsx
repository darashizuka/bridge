"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import UploadForm from "@/components/UploadForm";
import NotebookLoader from "@/components/NotebookLoader";
import type { ProgressEvent } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function DashboardPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState<ProgressEvent | null>(null);

  const handleSubmit = async (data: { file?: File; text?: string }) => {
    setIsLoading(true);
    setProgress({ step: "pending", progress: 0.05, message: "Uploading..." });

    try {
      const token = await getToken();
      const formData = new FormData();

      if (data.file) {
        formData.append("file", data.file);
        formData.append("file_name", data.file.name);
      } else if (data.text) {
        formData.append("text", data.text);
        formData.append("file_name", "pasted_notes.txt");
      }

      const res = await fetch(`${API_BASE}/analyses`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Upload failed");
      }

      const { id } = await res.json();

      const sseRes = await fetch(`${API_BASE}/analyses/${id}/progress`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!sseRes.ok || !sseRes.body) {
        router.push(`/dashboard/analysis/${id}`);
        return;
      }

      const reader = sseRes.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const evt: ProgressEvent = JSON.parse(line.slice(6));
            setProgress(evt);

            if (evt.step === "completed") {
              reader.cancel();
              router.push(`/dashboard/analysis/${id}`);
              return;
            } else if (evt.step === "failed") {
              reader.cancel();
              setIsLoading(false);
              setProgress(null);
              return;
            }
          } catch {}
        }
      }

      router.push(`/dashboard/analysis/${id}`);
    } catch (err: any) {
      setIsLoading(false);
      setProgress(null);
      alert(err.message || "Something went wrong.");
    }
  };

  return (
    <div className="flex flex-1 items-center justify-center px-8">
      {isLoading && progress ? (
        <NotebookLoader
          progress={progress.progress}
          message={progress.message}
        />
      ) : (
        <div className="flex flex-col items-center">
          <h2 className="mb-6 text-2xl font-semibold">New Analysis</h2>
          <UploadForm onSubmit={handleSubmit} isLoading={isLoading} />
        </div>
      )}
    </div>
  );
}
