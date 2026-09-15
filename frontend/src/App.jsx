import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "./useAuth";
import { listContracts, getContract } from "./api";
import LoginForm from "./components/LoginForm";
import ContractTable from "./components/ContractTable";
import ContractDetail from "./components/ContractDetail";
import UploadModal from "./components/UploadModal";
import RenewalsPanel from "./components/RenewalsPanel";
import {
  IconFileText,
  IconUpload,
  IconRefresh,
  IconLogOut,
  IconAlert,
  IconLayers,
  IconRepeat,
  IconClock,
} from "./components/Icons";
import { formatValueBreakdown, daysUntil, renewalActionDate } from "./format";

const RENEWAL_OPTIONS = [
  { value: "", label: "Any renewal type" },
  { value: "auto", label: "Auto-renews" },
  { value: "manual", label: "Manual renewal" },
];

const EXPIRY_OPTIONS = [
  { value: "", label: "Any expiry" },
  { value: "30", label: "Next 30 days" },
  { value: "60", label: "Next 60 days" },
  { value: "90", label: "Next 90 days" },
  { value: "overdue", label: "Already overdue" },
];

// Early CUAD test contracts loaded before the real demo-data set — kept in
// the backend, just hidden from this view. New uploads are unaffected.
const HIDDEN_CONTRACT_IDS = new Set([
  "bfbe4167-539d-47a0-83f4-e1cb5c9b8843", // Miltenyi Biotec GmbH
  "3c179755-35ff-4055-9ab9-288e960d089b", // Constellation NewEnergy, Inc.
  "731cab6c-814c-49ed-9238-9a1ff67588f6", // Photronics outsourcing agreement
  "a27e7149-aad9-4800-97ea-cf54cb1aa812", // Leader Act Ltd HK
  "b520f7e2-254c-421d-9d88-4033537216fc", // Mitchell's Web Advance, PLC
]);

export default function App() {
  const { user, checking, login, logout } = useAuth();
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedContract, setSelectedContract] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [renewalFilter, setRenewalFilter] = useState("");
  const [expiryFilter, setExpiryFilter] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const { contracts } = await listContracts();
      setContracts(contracts.filter((c) => !HIDDEN_CONTRACT_IDS.has(c.id)));
    } catch (err) {
      setLoadError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) refresh();
  }, [user, refresh]);

  useEffect(() => {
    if (!selectedId) {
      setSelectedContract(null);
      return;
    }
    getContract(selectedId).then(setSelectedContract).catch((err) => setLoadError(err.message));
  }, [selectedId]);

  const visibleContracts = useMemo(() => {
    return contracts.filter((c) => {
      if (renewalFilter === "auto" && !c.auto_renews) return false;
      if (renewalFilter === "manual" && c.auto_renews) return false;

      if (expiryFilter) {
        const actionDate = renewalActionDate(c);
        const days = actionDate ? daysUntil(actionDate) : null;
        if (days == null) return false;
        if (expiryFilter === "overdue") {
          if (days > 0) return false;
        } else if (days > Number(expiryFilter)) {
          return false;
        }
      }
      return true;
    });
  }, [contracts, renewalFilter, expiryFilter]);

  const stats = useMemo(() => {
    const total = contracts.length;
    const autoRenewing = contracts.filter((c) => c.auto_renews).length;
    const renewalsDue = contracts.filter((c) => {
      if (c.status !== "complete") return false;
      const actionDate = renewalActionDate(c);
      if (!actionDate) return false;
      const days = daysUntil(actionDate);
      return days <= 90;
    }).length;
    const totalValue = formatValueBreakdown(contracts);
    return { total, autoRenewing, renewalsDue, totalValue };
  }, [contracts]);

  if (checking) {
    return (
      <div className="login-wrap">
        <div className="spinner" style={{ width: 24, height: 24, color: "var(--accent)" }} />
      </div>
    );
  }

  if (!user) {
    return <LoginForm onLogin={login} />;
  }

  const displayName = user.signInDetails?.loginId || user.username || "User";
  const initials = displayName.slice(0, 1);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <IconFileText width={19} height={19} />
          </div>
          <div>
            <h1>Contract Review</h1>
            <div className="subtitle">Procurement contract intelligence · eu-west-2</div>
          </div>
        </div>
        <div className="topbar-right">
          <div className="user-chip">
            <span className="user-avatar">{initials}</span>
            {displayName}
          </div>
          <button className="ghost icon-btn" onClick={logout} title="Sign out">
            <IconLogOut />
          </button>
        </div>
      </header>

      <main>
        {selectedContract ? (
          <ContractDetail
            contract={selectedContract}
            onBack={() => setSelectedId(null)}
            onDeleted={() => {
              setSelectedId(null);
              refresh();
            }}
          />
        ) : (
          <>
            <div className="page-header">
              <div>
                <h2>Contracts</h2>
                <p className="page-desc">Track, review, and query every procurement agreement in one place.</p>
              </div>
              <button onClick={() => setShowUpload(true)}>
                <IconUpload width={15} height={15} />
                Upload contract
              </button>
            </div>

            <div className="stat-row">
              <div className="stat-card">
                <div className="stat-icon">
                  <IconLayers width={16} height={16} />
                </div>
                <div>
                  <div className="stat-label">Total contracts</div>
                  <div className="stat-value">{stats.total}</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">
                  <IconRepeat width={16} height={16} />
                </div>
                <div>
                  <div className="stat-label">Auto-renewing</div>
                  <div className="stat-value">{stats.autoRenewing}</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon accent">
                  <IconClock width={16} height={16} />
                </div>
                <div>
                  <div className="stat-label">Renewals due in 90 days</div>
                  <div className="stat-value accent">{stats.renewalsDue}</div>
                </div>
              </div>
            </div>

            <RenewalsPanel contracts={contracts} onSelect={setSelectedId} />

            <div className="card">
              <div className="toolbar">
                <div className="filter-group">
                  <label>Renewal</label>
                  <select value={renewalFilter} onChange={(e) => setRenewalFilter(e.target.value)}>
                    {RENEWAL_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="filter-group">
                  <label>Expiry</label>
                  <select value={expiryFilter} onChange={(e) => setExpiryFilter(e.target.value)}>
                    {EXPIRY_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
                <button className="secondary toolbar-refresh" onClick={refresh} disabled={loading}>
                  <IconRefresh width={14} height={14} className={loading ? "spin" : ""} />
                  {loading ? "Refreshing..." : "Refresh"}
                </button>
              </div>

              {loadError && (
                <div className="error-banner">
                  <IconAlert width={15} height={15} />
                  {loadError}
                </div>
              )}
              <ContractTable contracts={visibleContracts} loading={loading} onSelect={setSelectedId} onDeleted={refresh} />
            </div>
          </>
        )}
      </main>

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onUploaded={() => {
            setShowUpload(false);
            refresh();
          }}
        />
      )}
    </div>
  );
}
