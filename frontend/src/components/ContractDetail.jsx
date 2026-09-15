import { useEffect, useState } from "react";
import { askContract, deleteContract, viewContractFile } from "../api";
import { StatusBadge } from "./Badges";
import { IconArrowLeft, IconAlert, IconSparkle, IconExternalLink, IconTrash } from "./Icons";
import DeleteConfirmModal from "./DeleteConfirmModal";
import { formatCurrency, daysUntil, renewalActionDate } from "../format";

const OVERVIEW_FIELDS = [
  ["effective_date", "Effective date"],
  ["expiry_date", "Expiry date"],
  ["auto_renews", "Auto-renews"],
  ["renewal_notice_days", "Renewal notice (days)"],
  ["termination_notice_days", "Termination notice (days)"],
  ["termination_for_convenience", "Termination for convenience"],
  ["governing_law", "Governing law"],
  ["liability_cap_amount", "Liability cap"],
];

const COMMERCIAL_FIELDS = [
  ["contract_value_amount", "Contract value"],
  ["payment_terms_days", "Payment terms"],
  ["pricing_model", "Pricing model"],
  ["minimum_commitment", "Minimum commitment"],
  ["price_escalation_clause", "Price escalation"],
];

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "commercial", label: "Commercial" },
];

function formatValue(contract, key) {
  const v = contract[key];
  if (v === null || v === undefined || v === "") return null;
  if (typeof v === "boolean") return v ? "Yes" : "No";
  if (key === "contract_value_amount") return formatCurrency(v, contract.contract_value_currency) || String(v);
  if (key === "liability_cap_amount") return formatCurrency(v, contract.liability_cap_currency) || String(v);
  if (key === "payment_terms_days") return `Net ${v}`;
  return String(v);
}

function populatedRows(contract, fields) {
  const citationMap = contract.extraction_sources?.citations || {};
  return fields
    .map(([key, label]) => ({
      key,
      label,
      value: formatValue(contract, key),
      citations: citationMap[key] || [],
    }))
    .filter((row) => row.value !== null);
}

const RENEWAL_LOOKAHEAD_DAYS = 90;

const CITATION_RE = /\[(\d+)\]/g;

// Splits an answer like "Payment is due in 30 days [2]." into plain-text
// and citation pieces so each [n] can be rendered as a link to the exact
// source excerpt it's grounded in, instead of an inert bracketed number.
function renderAnswerWithCitations(text, sources, onCite) {
  const bySources = new Set(sources.map((s) => s.ref));
  const pieces = [];
  let last = 0;
  let match;
  CITATION_RE.lastIndex = 0;
  while ((match = CITATION_RE.exec(text))) {
    if (match.index > last) pieces.push(text.slice(last, match.index));
    const ref = Number(match[1]);
    if (bySources.has(ref)) {
      pieces.push(
        <button
          key={`${match.index}-${ref}`}
          type="button"
          className="qa-citation"
          onClick={() => onCite(ref)}
          title={`Jump to source excerpt ${ref}`}
        >
          {ref}
        </button>
      );
    } else {
      pieces.push(match[0]);
    }
    last = match.index + match[0].length;
  }
  if (last < text.length) pieces.push(text.slice(last));
  return pieces;
}

function SourceExcerpts({ excerpts, activeRef, onSelect }) {
  if (!excerpts || excerpts.length === 0) return null;
  return (
    <div className="qa-sources">
      <div className="qa-sources-title">Source excerpts — exactly where this is stated in the contract</div>
      {excerpts.map((s) => (
        <div
          key={s.ref}
          className={`qa-source ${activeRef === s.ref ? "active" : ""}`}
          onClick={() => onSelect(s.ref)}
        >
          <span className="qa-source-ref">[{s.ref}]</span>
          <span className="qa-source-text">{s.content}</span>
        </div>
      ))}
    </div>
  );
}

function renewalMetric(contract) {
  if (contract.status !== "complete") return { text: "—", className: "" };
  const actionDate = renewalActionDate(contract);
  if (!actionDate) return { text: "No expiry on file", className: "" };
  const days = daysUntil(actionDate);
  if (days <= 0) return { text: "Overdue", className: "danger" };
  if (days <= RENEWAL_LOOKAHEAD_DAYS) return { text: `${days} day${days === 1 ? "" : "s"}`, className: days <= 30 ? "danger" : "accent" };
  return { text: "No action needed", className: "" };
}

export default function ContractDetail({ contract, onBack, onDeleted }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("overview");
  const [activeSource, setActiveSource] = useState(null);
  const [activeExtractionRef, setActiveExtractionRef] = useState(null);
  const [fileError, setFileError] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [contract.id]);

  function handleViewFile() {
    setFileError(null);
    viewContractFile(contract.id).catch((err) => setFileError(err.message));
  }

  async function handleDelete() {
    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteContract(contract.id);
      onDeleted();
    } catch (err) {
      setDeleteError(err.message);
      setDeleting(false);
    }
  }

  async function handleAsk(e) {
    e.preventDefault();
    if (!question.trim()) return;
    setAsking(true);
    setError(null);
    setAnswer(null);
    setActiveSource(null);
    try {
      const result = await askContract(contract.id, question);
      setAnswer(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setAsking(false);
    }
  }

  const actionDate = contract.status === "complete" ? renewalActionDate(contract) : null;
  const actionDays = actionDate ? daysUntil(actionDate) : null;
  const showRenewalBanner = actionDays !== null && actionDays <= RENEWAL_LOOKAHEAD_DAYS;
  const renewal = renewalMetric(contract);
  const value = formatCurrency(contract.contract_value_amount, contract.contract_value_currency);

  const rows = tab === "overview" ? populatedRows(contract, OVERVIEW_FIELDS) : populatedRows(contract, COMMERCIAL_FIELDS);

  const allExcerpts = contract.extraction_sources?.excerpts || [];
  const rowRefs = new Set(rows.flatMap((r) => r.citations));
  const rowExcerpts = allExcerpts.filter((e) => rowRefs.has(e.ref));

  return (
    <div>
      <button className="back-link" onClick={onBack}>
        <IconArrowLeft width={15} height={15} />
        Back to contracts
      </button>

      <div className="card">
        <div className="detail-header">
          <div>
            <h2>{contract.vendor_name || contract.s3_key.split("/").pop()}</h2>
            <p className="file-path">
              {contract.category && <span className="category-pill" style={{ marginRight: 8 }}>{contract.category}</span>}
              {contract.s3_key}
            </p>
          </div>
          <div className="detail-badges">
            <StatusBadge status={contract.status} />
            <button type="button" className="secondary" onClick={handleViewFile}>
              <IconExternalLink width={14} height={14} />
              View original file
            </button>
            <button type="button" className="secondary danger-outline" onClick={() => setShowDeleteConfirm(true)}>
              <IconTrash width={14} height={14} />
              Delete
            </button>
          </div>
        </div>

        {fileError && (
          <div className="error-text" style={{ marginTop: 10 }}>
            <IconAlert width={14} height={14} />
            {fileError}
          </div>
        )}

        {contract.status === "processing" && (
          <div className="processing-banner">
            <span className="spinner" />
            Still processing — refresh in a moment to see extracted fields.
          </div>
        )}

        {showRenewalBanner && (
          <div className={`processing-banner renewal-banner ${actionDays <= 0 ? "overdue" : actionDays <= 30 ? "urgent" : ""}`}>
            <IconAlert width={14} height={14} />
            {actionDays <= 0
              ? `Renewal notice window has passed (was due ${actionDate}).`
              : `Act by ${actionDate} to avoid an unwanted auto-renewal (${actionDays} day${actionDays === 1 ? "" : "s"} left).`}
          </div>
        )}

        <div className="detail-metrics">
          <div className="detail-metric">
            <div className="label">Contract value</div>
            <div className="value-lg">{value || "—"}</div>
          </div>
          <div className="detail-metric">
            <div className="label">Renewal action</div>
            <div className={`value-lg ${renewal.className}`}>{renewal.text}</div>
          </div>
        </div>

        <div className="tab-bar">
          {TABS.map((t) => (
            <button key={t.id} className={`tab-btn ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </div>

        <div className="section" style={{ marginTop: 0, paddingTop: 0, borderTop: "none" }}>
          {rows.length > 0 ? (
            <div className="field-grid">
              {rows.map(({ key, label, value, citations }) => (
                <div className="field" key={key}>
                  <span className="label">{label}</span>
                  <span className="value">
                    {value}
                    {citations.map((ref) => (
                      <button
                        key={ref}
                        type="button"
                        className="qa-citation"
                        onClick={() => setActiveExtractionRef(ref)}
                        title={`Jump to source excerpt ${ref}`}
                      >
                        {ref}
                      </button>
                    ))}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted" style={{ margin: 0 }}>No data extracted for this section.</p>
          )}

          <SourceExcerpts excerpts={rowExcerpts} activeRef={activeExtractionRef} onSelect={setActiveExtractionRef} />
        </div>

        <div className="section qa-box">
          <h3 className="section-title">
            <IconSparkle width={15} height={15} style={{ color: "var(--accent)" }} />
            Ask this contract
          </h3>
          <form onSubmit={handleAsk} style={{ display: "flex", gap: 8 }}>
            <input
              style={{ flex: 1 }}
              placeholder="e.g. What happens if we terminate early?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button type="submit" disabled={asking}>
              {asking ? "Asking..." : "Ask"}
            </button>
          </form>
          {error && (
            <div className="error-text" style={{ marginTop: 10 }}>
              <IconAlert width={14} height={14} />
              {error}
            </div>
          )}
          {answer && (
            <div className="qa-answer">
              <div>{renderAnswerWithCitations(answer.answer, answer.sources || [], setActiveSource)}</div>
              <SourceExcerpts excerpts={answer.sources} activeRef={activeSource} onSelect={setActiveSource} />
            </div>
          )}
        </div>
      </div>

      {showDeleteConfirm && (
        <DeleteConfirmModal
          message={`This permanently deletes ${contract.vendor_name || contract.s3_key.split("/").pop()} and its extracted data, including the original file. This can't be undone.`}
          error={deleteError}
          busy={deleting}
          onCancel={() => setShowDeleteConfirm(false)}
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
}
