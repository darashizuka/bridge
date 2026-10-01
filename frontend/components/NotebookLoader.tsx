"use client";

import { useEffect, useState } from "react";

interface NotebookLoaderProps {
  progress?: number;
  message?: string;
}

export default function NotebookLoader({
  progress = 0,
  message,
}: NotebookLoaderProps) {
  const [page, setPage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setPage((p) => (p + 1) % 3), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Mini open book */}
      <div className="relative" style={{ width: 100, height: 72 }}>
        {/* Book spine shadow */}
        <div className="absolute left-1/2 top-2 bottom-0 w-px bg-[var(--color-primary)]/40" />

        {/* Left page (static) */}
        <div className="absolute left-0 top-0 w-[48px] h-[68px] rounded-l-md border border-[var(--color-border)] bg-[var(--color-card)] overflow-hidden">
          {[28, 34, 24, 30, 26].map((w, i) => (
            <div
              key={i}
              className="mx-2 mt-[10px] h-[2px] rounded-full bg-[var(--color-border)]"
              style={{ width: w }}
            />
          ))}
        </div>

        {/* Right page (static) */}
        <div className="absolute right-0 top-0 w-[48px] h-[68px] rounded-r-md border border-[var(--color-border)] bg-[var(--color-card)] overflow-hidden">
          {[22, 30, 26, 20, 28].map((w, i) => (
            <div
              key={i}
              className="mx-2 mt-[10px] h-[2px] rounded-full bg-[var(--color-border)]"
              style={{ width: w }}
            />
          ))}
        </div>

        {/* Flipping pages */}
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="absolute right-[2px] top-[1px] w-[46px] h-[66px] rounded-r-md border border-[var(--color-primary)]/20 bg-[var(--color-card)]"
            style={{
              transformOrigin: "left center",
              transform: page > i ? "rotateY(-180deg)" : "rotateY(0deg)",
              transition: "transform 0.7s cubic-bezier(0.4, 0, 0.2, 1)",
              zIndex: 3 - i,
              backfaceVisibility: "hidden",
            }}
          >
            {[18, 24, 20, 28].map((w, j) => (
              <div
                key={j}
                className="mx-2 mt-[11px] h-[2px] rounded-full bg-[var(--color-border)]/60"
                style={{ width: w }}
              />
            ))}
          </div>
        ))}
      </div>

      {/* Progress */}
      <div className="w-52 text-center">
        {progress > 0 && (
          <div className="mb-2 h-1 w-full overflow-hidden rounded-full bg-[var(--color-border)]">
            <div
              className="h-full rounded-full bg-[var(--color-primary)] transition-all duration-500"
              style={{ width: `${Math.max(progress * 100, 5)}%` }}
            />
          </div>
        )}
        <p className="text-xs text-[var(--color-muted)]">
          {message || "Preparing analysis..."}
        </p>
      </div>
    </div>
  );
}
