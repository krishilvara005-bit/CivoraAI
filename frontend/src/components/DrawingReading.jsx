const OK = ['read', 'partial'];

export default function DrawingReading({ reading, onReread }) {
  if (!reading) return null;
  const { state, status } = reading;
  if (state === 'pending') {
    return (
      <div className="rd" role="status" aria-live="polite">
        <b><span className="spin" aria-hidden="true" /> Reading your drawing…</b>
        <p>Looking for floors, overall size and rooms. This can take up to a minute. Details fill in by themselves.</p>
      </div>
    );
  }
  if (state === 'none') {
    return (
      <div className="rd">
        <b>Drawing not read yet</b>
        <p>CIVORA AI can fill in the property details from your 2D drawing.</p>
        <button type="button" className="btn sm" onClick={onReread}>Read drawing</button>
      </div>
    );
  }
  const ok = OK.includes(status);
  const rooms = reading.rooms || [];
  return (
    <div className="rd">
      <b>{ok ? 'Read from your drawing' : 'Could not read this drawing'}</b>
      {ok && (
        <ul>
          <li>Floors: <span className={reading.floors ? 'ok' : 'nt'}>{reading.floors || 'not found'}</span></li>
          <li>
            Plan size: <span className={reading.area ? 'ok' : 'nt'}>
              {reading.area ? `${reading.width_ft}' x ${reading.depth_ft}' = ${reading.area} sq ft per floor` : 'not found'}
            </span>
          </li>
          <li>Rooms found: <span className={rooms.length ? 'ok' : 'nt'}>{rooms.length || 'none'}</span></li>
        </ul>
      )}
      {(reading.warnings || []).map((w) => <p className="wn" key={w}>{w}</p>)}
      <p>{ok ? 'Check these against your drawing. Anything you type replaces the value read from it.' : 'Enter the details by hand.'}</p>
      <button type="button" className="btn ghost sm" onClick={onReread}>Read again</button>
    </div>
  );
}
