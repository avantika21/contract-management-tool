import { useState } from "react";
import { StatusBadge, AutoRenewBadge } from "./Badges";
import { IconInbox, IconChevronRight, IconExternalLink, IconTrash } from "./Icons";
import { formatCurrency } from "../format";
import { deleteContract, viewContractFile } from "../api";
import DeleteConfirmModal from "./DeleteConfirmModal";

function initialsFor(name) {
  if (!name) return "?";
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

function SkeletonRows() {
  return (
    <>
      {[...Array(5)].map((_, i) => (
        <tr key={i} className="skeleton-row">
          <td><div className="skeleton-bar" style={{ width: 140 }} /></td>
          <td><div className="skeleton-bar" style={{ width: 90 }} /></td>
          <td><div className="skeleton-bar" style={{ width: 80 }} /></td>
          <td><div className="skeleton-bar" style={{ width: 70 }} /></td>
          <td><div className="skeleton-bar" style={{ width: 80 }} /></td>
          <td></td>
          <td></td>
          <td></td>
        </tr>
      ))}
    </>
  );
}

export default function ContractTable({ contracts, onSelect, loading, onDeleted }) {
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  async function handleDelete() {
    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteContract(deleteTarget.id);
      setDeleteTarget(null);
      onDeleted?.();
    } catch (err) {
      setDeleteError(err.message);
    } finally {
      setDeleting(false);
    }
  }

  if (!loading && contracts.length === 0) {
    return (
      <div className="empty-state">
        <IconInbox width={32} height={32} className="empty-icon" />
        <div className="empty-title">No contracts yet</div>
        <p className="muted" style={{ margin: 0 }}>Upload a contract to start tracking it here.</p>
      </div>
    );
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Vendor</th>
            <th>Status</th>
            <th>Value</th>
            <th>Expiry</th>
            <th>Auto-renew</th>
            <th></th>
            <th></th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {loading && contracts.length === 0 ? (
            <SkeletonRows />
          ) : (
            contracts.map((c) => (
              <tr key={c.id} className="clickable" onClick={() => onSelect(c.id)}>
                <td>
                  {c.vendor_name ? (
                    <div className="vendor-cell">
                      <span className="vendor-avatar">{initialsFor(c.vendor_name)}</span>
                      {c.vendor_name}
                    </div>
                  ) : (
                    <span className="muted">—</span>
                  )}
                </td>
                <td><StatusBadge status={c.status} /></td>
                <td>
                  {formatCurrency(c.contract_value_amount, c.contract_value_currency) || (
                    <span className="muted">—</span>
                  )}
                </td>
                <td>{c.expiry_date || <span className="muted">—</span>}</td>
                <td><AutoRenewBadge autoRenews={c.auto_renews} /></td>
                <td className="row-view">
                  <button
                    type="button"
                    className="ghost icon-btn"
                    title="View original file"
                    onClick={(e) => {
                      e.stopPropagation();
                      viewContractFile(c.id).catch((err) => alert(err.message));
                    }}
                  >
                    <IconExternalLink width={15} height={15} />
                  </button>
                </td>
                <td className="row-chevron">
                  <IconChevronRight width={16} height={16} />
                </td>
                <td className="row-view">
                  <button
                    type="button"
                    className="ghost icon-btn danger-outline"
                    title="Delete contract"
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteError(null);
                      setDeleteTarget(c);
                    }}
                  >
                    <IconTrash width={15} height={15} />
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      {deleteTarget && (
        <DeleteConfirmModal
          message={`This permanently deletes ${deleteTarget.vendor_name || deleteTarget.s3_key.split("/").pop()} and its extracted data, including the original file. This can't be undone.`}
          error={deleteError}
          busy={deleting}
          onCancel={() => setDeleteTarget(null)}
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
}
