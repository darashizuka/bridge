export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(" ");
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function severityColor(severity: string): string {
  switch (severity) {
    case "high":
      return "bg-red-500";
    case "medium":
      return "bg-amber-500";
    case "low":
      return "bg-green-500";
    default:
      return "bg-gray-500";
  }
}

export function severityTextColor(severity: string): string {
  switch (severity) {
    case "high":
      return "text-red-400";
    case "medium":
      return "text-amber-400";
    case "low":
      return "text-green-400";
    default:
      return "text-gray-400";
  }
}
