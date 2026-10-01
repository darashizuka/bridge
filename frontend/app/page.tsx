import Link from "next/link";
import Navbar from "@/components/Navbar";
import { Show } from "@clerk/nextjs";
import { ArrowRight, BookOpen, Network, Brain } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />

      <main className="flex flex-1 flex-col items-center justify-center px-4">
        <div className="max-w-2xl text-center">
          <h1 className="text-5xl font-bold tracking-tight text-[var(--color-foreground)]">
            Upload lecture notes and{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              bridge gaps
            </span>{" "}
            in knowledge
          </h1>
          <p className="mt-4 text-lg text-[var(--color-muted)]">
            AI-powered analysis that finds what your lectures mention but never
            explain, fills those gaps with real sources, and builds you a
            personalized study guide.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Show when="signed-in">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-primary)] px-6 py-3 font-medium text-white hover:bg-[var(--color-primary-hover)] transition-colors"
              >
                Go to Dashboard
                <ArrowRight size={18} />
              </Link>
            </Show>
            <Show when="signed-out">
              <Link
                href="/sign-up"
                className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-primary)] px-6 py-3 font-medium text-white hover:bg-[var(--color-primary-hover)] transition-colors"
              >
                Get started
                <ArrowRight size={18} />
              </Link>
              <Link
                href="/sign-in"
                className="rounded-lg border border-[var(--color-border)] px-6 py-3 font-medium text-[var(--color-muted)] hover:text-[var(--color-foreground)] hover:border-[var(--color-muted)] transition-colors"
              >
                Log in
              </Link>
            </Show>
          </div>
        </div>

        <div className="mt-20 grid max-w-4xl grid-cols-1 gap-6 px-4 sm:grid-cols-3">
          {[
            {
              icon: BookOpen,
              title: "Gap Detection",
              desc: "Finds concepts mentioned but never explained in your notes.",
            },
            {
              icon: Network,
              title: "Dependency Graph",
              desc: "Visual map of what to study first based on concept relationships.",
            },
            {
              icon: Brain,
              title: "Flashcard Quiz",
              desc: "Interactive cards generated from your gaps to test understanding.",
            },
          ].map((f) => (
            <div
              key={f.title}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-6"
            >
              <f.icon size={24} className="text-[var(--color-primary)]" />
              <h3 className="mt-3 font-semibold">{f.title}</h3>
              <p className="mt-1 text-sm text-[var(--color-muted)]">{f.desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
