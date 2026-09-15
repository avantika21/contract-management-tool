import { formatCurrency, daysUntil, renewalActionDate } from "../format";
import { IconAlert, IconRepeat, IconClock } from "./Icons";

const LOOKAHEAD_DAYS = 90;

function urgencyTier(days) {
  if (days <= 0) return "high";
  if (days <= 30) return "medium";
  return "low";
}

function urgencyLabel(days) {
  if (days <= 0) return "Overdue";
  if (days === 1) return "1 day left";
  return `${days} days left`;
}

export default function RenewalsPanel({ contracts, onSelect }) {
  const upcoming = contracts
    .filter((c) => c.status === "complete")
    .map((c) => ({ contract: c, actionDate: renewalActionDate(c) }))
    .filter(({ actionDate }) => actionDate && daysUntil(actionDate) <= LOOKAHEAD_DAYS)
    .sort((a, b) => new Date(a.actionDate) - new Date(b.actionDate));

  if (upcoming.length === 0) return null;

  return (
    <div className="card renewals-panel">
      <h3 className="section-title">
        <IconAlert width={15} height={15} style={{ color: "var(--risk-medium)" }} />
        Renewals needing action (next {LOOKAHEAD_DAYS} days)
      </h3>
      <div className="renewal-list">
        {upcoming.map(({ contract, actionDate }) => {
          const days = daysUntil(actionDate);
          const tier = urgencyTier(days);
          const value = formatCurrency(contract.contract_value_amount, contract.contract_value_currency);
          return (
            <div
              className={`renewal-card tier-${tier}`}
              key={contract.id}
              onClick={() => onSelect(contract.id)}
            >
              <div className="renewal-main">
                <div className="renewal-vendor">{contract.vendor_name || contract.s3_key.split("/").pop()}</div>
                <div className="renewal-tags">
                  <span className={`reason-tag ${contract.auto_renews ? "auto" : "manual"}`}>
                    {contract.auto_renews ? (
                      <IconRepeat width={11} height={11} />
                    ) : (
                      <IconClock width={11} height={11} />
                    )}
                    {contract.auto_renews ? "Auto-renews — cancel to avoid renewal" : "Manual renewal needed"}
                  </span>
                  {value && <span className="muted">{value}</span>}
                </div>
              </div>
              <div className="renewal-meta">
                <div className="muted">Act by {actionDate}</div>
                <span className={`badge risk-${tier}`}>{urgencyLabel(days)}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
