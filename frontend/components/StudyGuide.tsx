"use client";

import ReactMarkdown from "react-markdown";

interface StudyGuideProps {
  content: string;
}

export default function StudyGuide({ content }: StudyGuideProps) {
  if (!content) {
    return (
      <p className="text-[var(--color-muted)]">No study guide generated.</p>
    );
  }

  return (
    <div className="prose prose-invert max-w-none prose-headings:text-[var(--color-foreground)] prose-p:text-[var(--color-muted)] prose-strong:text-[var(--color-foreground)] prose-a:text-[var(--color-primary)] prose-blockquote:border-[var(--color-primary)]/50 prose-blockquote:text-[var(--color-muted)] prose-hr:border-[var(--color-border)]">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
