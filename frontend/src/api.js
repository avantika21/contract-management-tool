import { fetchAuthSession } from "aws-amplify/auth";
import { API_ENDPOINT } from "./aws-config";

async function authHeader() {
  const session = await fetchAuthSession();
  const token = session.tokens?.idToken?.toString();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(await authHeader()),
    ...(options.headers || {}),
  };
  const resp = await fetch(`${API_ENDPOINT}${path}`, { ...options, headers });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.error || `Request failed: ${resp.status}`);
  }
  return resp.status === 204 ? null : resp.json();
}

export function listContracts(filters = {}) {
  const params = new URLSearchParams(filters);
  const qs = params.toString() ? `?${params}` : "";
  return request(`/contracts${qs}`);
}

export function getContract(contractId) {
  return request(`/contracts/${contractId}`);
}

export function getContractFileUrl(contractId) {
  return request(`/contracts/${contractId}/file-url`);
}

// Opens a blank tab synchronously (within the click gesture) then points it
// at the presigned URL once fetched, so browsers don't block it as a popup.
export async function viewContractFile(contractId) {
  const tab = window.open("", "_blank");
  try {
    const { url } = await getContractFileUrl(contractId);
    if (tab) tab.location = url;
    else window.open(url, "_blank");
  } catch (err) {
    if (tab) tab.close();
    throw err;
  }
}

export function deleteContract(contractId) {
  return request(`/contracts/${contractId}`, { method: "DELETE" });
}

export function askContract(contractId, question) {
  return request(`/contracts/${contractId}/ask`, {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

export function createUploadUrl({ vendor, filename }) {
  return request("/uploads", {
    method: "POST",
    body: JSON.stringify({ vendor, filename }),
  });
}

export async function uploadFileToS3(uploadUrl, file) {
  const resp = await fetch(uploadUrl, {
    method: "PUT",
    headers: { "Content-Type": "application/pdf" },
    body: file,
  });
  if (!resp.ok) {
    throw new Error(`Upload failed: ${resp.status}`);
  }
}
