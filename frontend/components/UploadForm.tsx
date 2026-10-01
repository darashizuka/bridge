"use client";

import { useState, useRef, useCallback } from "react";
import { Upload, FileText, X, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadFormProps {
  onSubmit: (data: { file?: File; text?: string }) => void;
  isLoading: boolean;
}

const ACCEPTED = ".pdf,.pptx,.txt";
const MAX_SIZE_MB = 10;
const MAX_TEXT_CHARS = 100_000;

export default function UploadForm({ onSubmit, isLoading }: UploadFormProps) {
  const [tab, setTab] = useState<"file" | "text">("file");
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = (f: File): string | null => {
    const ext = f.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "pptx", "txt"].includes(ext || "")) {
      return "Unsupported format. Use PDF, PPTX, or TXT.";
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File exceeds ${MAX_SIZE_MB}MB limit.`;
    }
    return null;
  };

  const handleFile = (f: File) => {
    const err = validateFile(f);
    if (err) {
      setError(err);
      return;
    }
    setError("");
    setFile(f);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, []);

  const handleSubmit = () => {
    if (tab === "file") {
      if (!file) {
        setError("Please select a file.");
        return;
      }
      onSubmit({ file });
    } else {
      if (!text.trim()) {
        setError("Please paste some notes.");
        return;
      }
      if (text.length > MAX_TEXT_CHARS) {
        setError(`Text exceeds ${MAX_TEXT_CHARS.toLocaleString()} character limit.`);
        return;
      }
      onSubmit({ text });
    }
  };

  return (
    <div className="w-full max-w-md">
      <div className="mb-4 flex rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-1">
        {(["file", "text"] as const).map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setError(""); }}
            className={cn(
              "flex-1 rounded-md py-2 text-sm font-medium transition-colors",
              tab === t
                ? "bg-[var(--color-primary)] text-white"
                : "text-[var(--color-muted)] hover:text-[var(--color-foreground)]"
            )}
          >
            {t === "file" ? "Upload File" : "Paste Text"}
          </button>
        ))}
      </div>

      {tab === "file" ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 transition-colors",
            dragActive
              ? "border-[var(--color-primary)] bg-[var(--color-primary)]/5"
              : "border-[var(--color-border)] hover:border-[var(--color-muted)]"
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED}
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />
          {file ? (
            <div className="flex items-center gap-3">
              <FileText size={20} className="text-[var(--color-primary)]" />
              <span className="text-sm font-medium">{file.name}</span>
              <button
                onClick={(e) => { e.stopPropagation(); setFile(null); }}
                className="text-[var(--color-muted)] hover:text-[var(--color-foreground)]"
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <>
              <Upload size={32} className="text-[var(--color-muted)]" />
              <p className="mt-3 text-sm text-[var(--color-muted)]">
                Drop your file here or click to browse
              </p>
              <p className="mt-1 text-xs text-[var(--color-muted)]/60">
                PDF, PPTX, TXT up to {MAX_SIZE_MB}MB
              </p>
            </>
          )}
        </div>
      ) : (
        <div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste your lecture notes here..."
            rows={12}
            className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-4 text-sm text-[var(--color-foreground)] placeholder:text-[var(--color-muted)] focus:border-[var(--color-primary)] focus:outline-none resize-none"
          />
          <p className="mt-1 text-right text-xs text-[var(--color-muted)]">
            {text.length.toLocaleString()} / {MAX_TEXT_CHARS.toLocaleString()}
          </p>
        </div>
      )}

      {error && (
        <div className="mt-3 flex items-center gap-2 text-sm text-red-400">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={isLoading}
        className="mt-4 w-full rounded-lg bg-[var(--color-primary)] py-3 font-medium text-white hover:bg-[var(--color-primary-hover)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? "Analyzing..." : "Analyze"}
      </button>
    </div>
  );
}
