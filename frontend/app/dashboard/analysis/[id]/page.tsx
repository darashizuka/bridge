"use client";

import { useEffect, useState, use } from "react";
import { useAuth } from "@clerk/nextjs";
import { BookOpen, Network, Brain, ArrowLeft, AlertCircle } from "lucide-react";
import Link from "next/link";
import { cn, severityColor } from "@/lib/utils";
import StudyGuide from "@/components/StudyGuide";
import DependencyGraph from "@/components/DependencyGraph";
import FlashcardDeck from "@/components/FlashcardDeck";
import NotebookLoader from "@/components/NotebookLoader";
import type { AnalysisDetail, GraphResponse, ProgressEvent } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

type Tab = "guide" | "graph" | "flashcards";

export default function AnalysisPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { getToken } = useAuth();
  const [analysis, setAnalysis] = useState<AnalysisDetail | null>(null);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [tab, setTab] = useState<Tab>("guide");
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = await getToken();
        const headers = { Authorization: `Bearer ${token}` };

        const res = await fetch(`${API_BASE}/analyses/${id}`, { headers });
        if (!res.ok) throw new Error("Analysis not found");

        const data: AnalysisDetail = await res.json();
        setAnalysis(data);

        if (data.status === "completed") {
          const graphRes = await fetch(`${API_BASE}/analyses/${id}/graph`, {
            headers,
          });
          if (graphRes.ok) {
            setGraph(await graphRes.json());
          }
          setLoading(false);
        } else if (data.status === "failed") {
          setError(data.error_message || "Analysis failed");
          setLoading(false);
        } else {
          const sseRes = await fetch(`${API_BASE}/analyses/${id}/progress`, {
            headers,
          });

          if (!sseRes.ok || !sseRes.body) {
            setTimeout(fetchData, 3000);
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
                const prog: ProgressEvent = JSON.parse(line.slice(6));
                setProgress(prog);

                if (prog.step === "completed") {
                  reader.cancel();
                  fetchData();
                  return;
                } else if (prog.step === "failed") {
                  reader.cancel();
                  setError(prog.message);
                  setLoading(false);
                  return;
                }
              } catch {}
            }
          }

          setTimeout(fetchData, 3000);
        }
      } catch (err: any) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
  }, [id, getToken]);

  const handleUpdateMastery = async (
    flashcardId: string,
    mastery: "known" | "unknown"
  ) => {
    try {
      const token = await getToken();
      await fetch(`${API_BASE}/analyses/${id}/flashcards/${flashcardId}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mastery }),
      });
    } catch {}
  };

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <NotebookLoader
          currentStep={progress?.step}
          progress={progress?.progress}
          message={progress?.message}
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4">
        <AlertCircle size={48} className="text-red-400" />
        <p className="text-red-400">{error}</p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 text-sm text-[var(--color-primary)] hover:underline"
        >
          <ArrowLeft size={16} />
          Back to dashboard
        </Link>
      </div>
    );
  }

  if (!analysis) return null;

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: "guide", label: "Study Guide", icon: BookOpen },
    { key: "graph", label: "Concept Map", icon: Network },
    { key: "flashcards", label: "Flashcards", icon: Brain },
  ];

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link
            href="/dashboard"
            className="mb-2 inline-flex items-center gap-1 text-xs text-[var(--color-muted)] hover:text-[var(--color-foreground)]"
          >
            <ArrowLeft size={14} />
            Back
          </Link>
          <h1 className="text-2xl font-semibold">{analysis.display_name}</h1>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {analysis.filled_gap_count} of {analysis.gap_count} gaps analyzed
          </p>
        </div>
      </div>

      <div className="mb-6 flex gap-4">
        {(["high", "medium", "low"] as const).map((sev) => {
          const count = analysis.gaps.filter((g) => g.severity === sev).length;
          return (
            <div
              key={sev}
              className="flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] px-3 py-2"
            >
              <div className={`h-2.5 w-2.5 rounded-full ${severityColor(sev)}`} />
              <span className="text-sm capitalize">{sev}</span>
              <span className="text-sm font-semibold">{count}</span>
            </div>
          );
        })}
      </div>

      <div className="mb-6 flex gap-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors",
              tab === t.key
                ? "bg-[var(--color-primary)] text-white"
                : "text-[var(--color-muted)] hover:text-[var(--color-foreground)]"
            )}
          >
            <t.icon size={16} />
            {t.label}
          </button>
        ))}
      </div>

      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-6">
        {tab === "guide" && (
          <StudyGuide content={analysis.study_guide || ""} />
        )}
        {tab === "graph" && graph && <DependencyGraph data={graph} />}
        {tab === "graph" && !graph && (
          <p className="text-[var(--color-muted)]">
            No dependency data available.
          </p>
        )}
        {tab === "flashcards" && (
          <FlashcardDeck
            flashcards={analysis.flashcards}
            onUpdateMastery={handleUpdateMastery}
          />
        )}
      </div>
    </div>
  );
}
