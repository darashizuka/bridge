"use client";

import Link from "next/link";
import { UserButton, Show } from "@clerk/nextjs";
import { History } from "lucide-react";

interface NavbarProps {
  onHistoryClick?: () => void;
}

export default function Navbar({ onHistoryClick }: NavbarProps) {
  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--color-border)] bg-[var(--color-background)]/80 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Show when="signed-in">
          <button
            onClick={onHistoryClick}
            className="flex items-center gap-2 text-sm text-[var(--color-muted)] hover:text-[var(--color-foreground)] transition-colors"
          >
            <History size={18} />
            <span>History</span>
          </button>
        </Show>
        <Show when="signed-out">
          <div />
        </Show>

        <Link
          href="/"
          className="text-lg font-semibold tracking-tight text-[var(--color-foreground)]"
        >
          Bridge
        </Link>

        <Show when="signed-in">
          <UserButton />
        </Show>
        <Show when="signed-out">
          <div className="flex items-center gap-3">
            <Link
              href="/sign-in"
              className="text-sm text-[var(--color-muted)] hover:text-[var(--color-foreground)] transition-colors"
            >
              Log in
            </Link>
            <Link
              href="/sign-up"
              className="rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-primary-hover)] transition-colors"
            >
              Sign up
            </Link>
          </div>
        </Show>
      </div>
    </nav>
  );
}
