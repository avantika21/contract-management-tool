import { IconAlert, IconX } from "./Icons";

export default function DeleteConfirmModal({ title = "Delete contract?", message, error, busy, onCancel, onConfirm }) {
  return (
    <div className="modal-backdrop" onClick={() => !busy && onCancel()}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button type="button" className="ghost icon-btn" onClick={onCancel} disabled={busy}>
            <IconX width={16} height={16} />
          </button>
        </div>

        <p className="muted" style={{ margin: 0 }}>
          {message}
        </p>

        {error && (
          <div className="error-text">
            <IconAlert width={14} height={14} />
            {error}
          </div>
        )}

        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button type="button" className="secondary" onClick={onCancel} disabled={busy}>
            Cancel
          </button>
          <button type="button" className="danger" onClick={onConfirm} disabled={busy}>
            {busy ? "Deleting..." : "Delete contract"}
          </button>
        </div>
      </div>
    </div>
  );
}
