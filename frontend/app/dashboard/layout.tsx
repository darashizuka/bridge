"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import Navbar from "@/components/Navbar";
import HistorySidebar from "@/components/HistorySidebar";
import type { AnalysisListItem } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { getToken } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [analyses, setAnalyses] = useState<AnalysisListItem[]>([]);

  const fetchAnalyses = useCallback(async () => {
    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/analyses`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setAnalyses(await res.json());
      }
    } catch {}
  }, [getToken]);

  useEffect(() => {
    fetchAnalyses();
  }, [fetchAnalyses]);

  const handleDelete = async (id: string) => {
    try {
      const token = await getToken();
      await fetch(`${API_BASE}/analyses/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      setAnalyses((prev) => prev.filter((a) => a.id !== id));
    } catch {}
  };

  const handleRename = async (id: string, name: string) => {
    try {
      const token = await getToken();
      await fetch(`${API_BASE}/analyses/${id}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ display_name: name }),
      });
      setAnalyses((prev) =>
        prev.map((a) => (a.id === id ? { ...a, display_name: name } : a))
      );
    } catch {}
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar onHistoryClick={() => setSidebarOpen(true)} />
      <HistorySidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        analyses={analyses}
        onDelete={handleDelete}
        onRename={handleRename}
      />
      <main className="flex flex-1">{children}</main>
    </div>
  );
}
