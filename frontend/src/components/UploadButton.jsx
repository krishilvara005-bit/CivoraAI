import { useRef, useState } from 'react';
import { ALLOWED, api } from '../api.js';

export default function UploadButton({ projectId, onUploaded, className = 'btn', label = 'Upload plan from computer' }) {
  const input = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function pick(e) {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setBusy(true);
    setError('');
    try {
      onUploaded(await api.uploadPlan(projectId, file));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button type="button" className={className} disabled={busy} onClick={() => input.current.click()}>
        {busy ? 'Uploading…' : label}
      </button>
      <input ref={input} type="file" hidden accept={ALLOWED} onChange={pick} />
      {error && <p className="ferr" role="alert">{error}</p>}
    </>
  );
}
