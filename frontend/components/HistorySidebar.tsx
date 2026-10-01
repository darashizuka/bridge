"use client";

import { useState } from "react";
import Link from "next/link";
import { X, Search, Trash2, Pencil, Check, FileText } from "lucide-react";
import { cn, formatDate } from "@/lib/utils";
import type { AnalysisListItem } from "@/lib/types";

interface HistorySidebarProps {
  open: boolean;
  onClose: () => void;
  analyses: AnalysisListItem[];
  onDelete: (id: string) => void;
  onRename: (id: string, name: string) => void;
}

export default function HistorySidebar({
  open,
  onClose,
  analyses,
  onDelete,
  onRename,
}: HistorySidebarProps) {
  const [search, setSearch] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const filtered = analyses.filter((a) =>
    a.display_name.toLowerCase().includes(search.toLowerCase())
  );

  const startEdit = (a: AnalysisListItem) => {
    setEditingId(a.id);
    setEditValue(a.display_name);
  };

  const confirmEdit = (id: string) => {
    if (editValue.trim()) {
      onRename(id, editValue.trim());
    }
    setEditingId(null);
  };

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50"
          onClick={onClose}
        />
      )}

      <aside
        className={cn(
          "fixed left-0 top-0 z-50 flex h-full w-80 flex-col border-r border-[var(--color-border)] bg-[var(--color-background)] transition-transform duration-300",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center justify-between border-b border-[var(--color-border)] p-4">
          <h2 className="font-semibold">History</h2>
          <button
            onClick={onClose}
            className="text-[var(--color-muted)] hover:text-[var(--color-foreground)]"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-3">
          <div className="relative">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-muted)]"
            />
            <input
              type="text"
              placeholder="Search sessions..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] py-2 pl-9 pr-3 text-sm text-[var(--color-foreground)] placeholder:text-[var(--color-muted)] focus:border-[var(--color-primary)] focus:outline-none"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-3 pb-3">
          {filtered.length === 0 ? (
            <p className="mt-8 text-center text-sm text-[var(--color-muted)]">
              No sessions found.
            </p>
          ) : (
            <ul className="space-y-1">
              {filtered.map((a) => (
                <li
                  key={a.id}
                  className="group rounded-lg border border-transparent hover:border-[var(--color-border)] hover:bg-[var(--color-card)]"
                >
                  <div className="flex items-start gap-3 p-3">
                    <FileText
                      size={16}
                      className="mt-0.5 shrink-0 text-[var(--color-muted)]"
                    />
                    <div className="min-w-0 flex-1">
                      {editingId === a.id ? (
                        <div className="flex items-center gap-1">
                          <input
                            autoFocus
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onKeyDown={(e) =>
                              e.key === "Enter" && confirmEdit(a.id)
                            }
                            className="w-full rounded border border-[var(--color-primary)] bg-transparent px-1 text-sm focus:outline-none"
                          />
                          <button onClick={() => confirmEdit(a.id)}>
                            <Check size={14} className="text-green-400" />
                          </button>
                        </div>
                      ) : (
                        <Link
                          href={`/dashboard/analysis/${a.id}`}
                          onClick={onClose}
                          className="block truncate text-sm font-medium hover:text-[var(--color-primary)]"
                        >
                          {a.display_name}
                        </Link>
                      )}
                      <div className="mt-1 flex items-center gap-2 text-xs text-[var(--color-muted)]">
                        <span>{formatDate(a.created_at)}</span>
                        {a.gap_count > 0 && (
                          <span className="rounded bg-[var(--color-card)] px-1.5 py-0.5">
                            {a.gap_count} gaps
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex shrink-0 gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => startEdit(a)}
                        className="p-1 text-[var(--color-muted)] hover:text-[var(--color-foreground)]"
                      >
                        <Pencil size={14} />
                      </button>
                      <button
                        onClick={() => onDelete(a.id)}
                        className="p-1 text-[var(--color-muted)] hover:text-red-400"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>
    </>
  );
}
