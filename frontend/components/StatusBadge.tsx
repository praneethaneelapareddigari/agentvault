export default function StatusBadge({ status }: { status: string }) {
  const s = status.toUpperCase();
  const cls =
    s === "PASS" || s === "CONFIRMED" || s === "DONE" || s === "EXECUTED"
      ? "badge-pass"
      : s === "FAIL" || s === "FAILED" || s === "REJECTED"
      ? "badge-fail"
      : "badge-pending";
  return (
    <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${cls}`}>
      {s}
    </span>
  );
}
