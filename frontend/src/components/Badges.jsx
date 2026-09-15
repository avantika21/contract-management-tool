const STATUS_LABELS = {
  processing: "Processing",
  complete: "Complete",
  failed: "Failed",
};

export function StatusBadge({ status }) {
  return <span className={`badge status-${status}`}>{STATUS_LABELS[status] || status}</span>;
}

export function AutoRenewBadge({ autoRenews }) {
  if (autoRenews == null) return <span className="muted">—</span>;
  return (
    <span className={`badge ${autoRenews ? "auto-renew-yes" : "auto-renew-no"}`}>
      {autoRenews ? "Yes" : "No"}
    </span>
  );
}
