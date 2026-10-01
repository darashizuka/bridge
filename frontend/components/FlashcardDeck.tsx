"use client";

import { useState, useCallback } from "react";
import { RotateCcw, Check, X } from "lucide-react";
import { cn, severityColor, severityTextColor } from "@/lib/utils";
import type { FlashcardResponse } from "@/lib/types";

interface FlashcardDeckProps {
  flashcards: FlashcardResponse[];
  onUpdateMastery: (id: string, mastery: "known" | "unknown") => void;
}

export default function FlashcardDeck({
  flashcards,
  onUpdateMastery,
}: FlashcardDeckProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [queue, setQueue] = useState<FlashcardResponse[]>([...flashcards]);
  const [results, setResults] = useState<{ known: number; unknown: number }>({
    known: 0,
    unknown: 0,
  });
  const [finished, setFinished] = useState(false);

  const current = queue[currentIndex];
  const total = flashcards.length;
  const reviewed = results.known + results.unknown;

  const handleMark = useCallback(
    (mastery: "known" | "unknown") => {
      if (!current) return;

      onUpdateMastery(current.id, mastery);

      const newResults = { ...results, [mastery]: results[mastery] + 1 };
      setResults(newResults);

      if (mastery === "unknown") {
        setQueue((prev) => [...prev, current]);
      }

      setFlipped(false);

      if (currentIndex + 1 >= queue.length) {
        if (mastery === "known") {
          setFinished(true);
          return;
        }
      }

      setTimeout(() => {
        if (currentIndex + 1 < queue.length) {
          setCurrentIndex((i) => i + 1);
        } else if (mastery === "unknown") {
          setCurrentIndex((i) => i + 1);
        } else {
          setFinished(true);
        }
      }, 200);
    },
    [current, currentIndex, queue, results, onUpdateMastery]
  );

  const restart = () => {
    setQueue([...flashcards]);
    setCurrentIndex(0);
    setFlipped(false);
    setResults({ known: 0, unknown: 0 });
    setFinished(false);
  };

  if (flashcards.length === 0) {
    return (
      <p className="text-[var(--color-muted)]">No flashcards available.</p>
    );
  }

  if (finished) {
    return (
      <div className="flex flex-col items-center gap-6 py-12">
        <h3 className="text-xl font-semibold">Session Complete</h3>
        <div className="flex gap-8">
          <div className="text-center">
            <p className="text-3xl font-bold text-green-400">{results.known}</p>
            <p className="text-sm text-[var(--color-muted)]">Known</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold text-amber-400">
              {results.unknown}
            </p>
            <p className="text-sm text-[var(--color-muted)]">Still learning</p>
          </div>
        </div>
        <div className="h-2 w-64 overflow-hidden rounded-full bg-[var(--color-border)]">
          <div
            className="h-full bg-green-500 transition-all"
            style={{
              width: `${total > 0 ? (results.known / total) * 100 : 0}%`,
            }}
          />
        </div>
        <p className="text-sm text-[var(--color-muted)]">
          {results.known} of {total} concepts mastered
        </p>
        <button
          onClick={restart}
          className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm hover:bg-[var(--color-card)] transition-colors"
        >
          <RotateCcw size={16} />
          Restart
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Progress bar */}
      <div className="w-full max-w-md">
        <div className="flex justify-between text-xs text-[var(--color-muted)] mb-1">
          <span>
            Card {Math.min(reviewed + 1, total)} of {total}
          </span>
          <span>{results.known} known</span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--color-border)]">
          <div
            className="h-full bg-[var(--color-primary)] transition-all duration-300"
            style={{ width: `${(reviewed / total) * 100}%` }}
          />
        </div>
      </div>

      {/* Card */}
      <div
        className={cn("flip-card w-full max-w-md", flipped && "flipped")}
        style={{ height: 280 }}
        onClick={() => setFlipped(!flipped)}
      >
        <div className="flip-card-inner relative w-full h-full">
          {/* Front */}
          <div className="flip-card-front flex flex-col items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-8 cursor-pointer">
            <div className="mb-4 flex items-center gap-2">
              <div
                className={`h-2 w-2 rounded-full ${severityColor(current?.severity || "medium")}`}
              />
              <span
                className={`text-xs font-medium ${severityTextColor(current?.severity || "medium")}`}
              >
                {current?.severity?.toUpperCase()}
              </span>
            </div>
            <p className="text-center text-lg font-medium">
              {current?.question}
            </p>
            <p className="mt-4 text-xs text-[var(--color-muted)]">
              Click to reveal answer
            </p>
          </div>

          {/* Back */}
          <div className="flip-card-back flex flex-col items-center justify-center rounded-xl border border-[var(--color-primary)]/30 bg-[var(--color-card)] p-8">
            <p className="text-xs font-medium text-[var(--color-primary)] mb-3">
              {current?.concept}
            </p>
            <p className="text-center text-[var(--color-foreground)]">
              {current?.answer}
            </p>
          </div>
        </div>
      </div>

      {/* Actions */}
      {flipped && (
        <div className="flex gap-4">
          <button
            onClick={() => handleMark("unknown")}
            className="inline-flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-6 py-2.5 text-sm font-medium text-amber-400 hover:bg-amber-500/20 transition-colors"
          >
            <X size={16} />
            Still learning
          </button>
          <button
            onClick={() => handleMark("known")}
            className="inline-flex items-center gap-2 rounded-lg border border-green-500/30 bg-green-500/10 px-6 py-2.5 text-sm font-medium text-green-400 hover:bg-green-500/20 transition-colors"
          >
            <Check size={16} />
            Got it
          </button>
        </div>
      )}
    </div>
  );
}
