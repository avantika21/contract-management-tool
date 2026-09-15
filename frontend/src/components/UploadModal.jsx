import { useEffect, useRef, useState } from "react";
import { createUploadUrl, listContracts, uploadFileToS3 } from "../api";
import { IconUpload, IconX, IconAlert, IconFileText } from "./Icons";

// S3 key prefix for uploads — purely organizational; the real vendor name is
// filled in later by the extraction pipeline once it reads the document.
const UPLOAD_FOLDER = "uploads";
const POLL_INTERVAL_MS = 4000;
// Textract + field extraction usually takes a minute or two; give up
// auto-polling well past that so a stuck pipeline doesn't hang the modal.
const POLL_TIMEOUT_MS = 6 * 60 * 1000;

export default function UploadModal({ onClose, onUploaded }) {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [stuck, setStuck] = useState(false);
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);
  const uploadKeyRef = useRef(null);
  const onUploadedRef = useRef(onUploaded);
  onUploadedRef.current = onUploaded;

  function handleFileChange(f) {
    if (f && f.type === "application/pdf") {
      setFile(f);
      setError(null);
    } else if (f) {
      setError("Please choose a PDF file.");
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const { upload_url, key } = await createUploadUrl({
        vendor: UPLOAD_FOLDER,
        filename: file.name.replace(/[^a-zA-Z0-9._-]+/g, "_"),
      });
      await uploadFileToS3(upload_url, file);
      uploadKeyRef.current = key;
      setProcessing(true);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  // Once the file is in S3, poll the contracts list for the row the
  // pipeline creates for this upload and wait for it to reach 'complete',
  // then hand off to the main page automatically — no manual "Done" click.
  useEffect(() => {
    if (!processing) return;
    let cancelled = false;
    const startedAt = Date.now();

    async function poll() {
      try {
        const { contracts } = await listContracts();
        const match = contracts.find((c) => c.s3_key === uploadKeyRef.current);
        if (match && match.status === "complete") {
          if (!cancelled) onUploadedRef.current();
          return;
        }
      } catch {
        // transient — just retry on the next tick
      }
      if (cancelled) return;
      if (Date.now() - startedAt > POLL_TIMEOUT_MS) {
        setStuck(true);
        return;
      }
      timer = setTimeout(poll, POLL_INTERVAL_MS);
    }

    let timer = setTimeout(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [processing]);

  if (processing) {
    return (
      <div className="modal-backdrop" onClick={stuck ? onUploaded : undefined}>
        <div className="modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>Upload contract</h3>
          </div>
          <div className="upload-processing">
            <div className="spinner" style={{ width: 28, height: 28, color: "var(--accent)" }} />
            {stuck ? (
              <p>Still processing — this is taking longer than usual. You can close this now; the contract will appear in the list once it's done.</p>
            ) : (
              <p>Upload complete. Your contract is being processed — you'll be taken back to the list automatically once it's ready.</p>
            )}
          </div>
          {stuck && (
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
              <button type="button" onClick={onUploaded}>
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="modal-backdrop" onClick={busy ? undefined : onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <div className="modal-header">
          <h3>Upload contract</h3>
          <button type="button" className="ghost icon-btn" onClick={onClose} disabled={busy}>
            <IconX width={16} height={16} />
          </button>
        </div>

        <label className="field">
          <span className="label">PDF file</span>
          <div
            className={`dropzone ${dragging ? "dragging" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              handleFileChange(e.dataTransfer.files[0]);
            }}
          >
            {file ? (
              <>
                <IconFileText width={22} height={22} style={{ color: "var(--accent)" }} />
                <span className="filename">{file.name}</span>
                <span className="muted">Click or drop to replace</span>
              </>
            ) : (
              <>
                <IconUpload width={22} height={22} />
                <span>Drag a PDF here, or click to browse</span>
              </>
            )}
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => handleFileChange(e.target.files[0])}
              required={!file}
              disabled={busy}
            />
          </div>
        </label>

        {error && (
          <div className="error-text">
            <IconAlert width={14} height={14} />
            {error}
          </div>
        )}

        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button type="button" className="secondary" onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button type="submit" disabled={busy || !file}>
            {busy && <span className="spinner" />}
            {busy ? "Uploading..." : "Upload"}
          </button>
        </div>
      </form>
    </div>
  );
}
