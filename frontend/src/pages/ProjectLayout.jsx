import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, NavLink, Outlet, useParams } from 'react-router-dom';
import { api } from '../api.js';

export default function ProjectLayout() {
  const { id } = useParams();
  const [status, setStatus] = useState({ state: 'loading' });
  const [project, setProject] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [reading, setReading] = useState(null);
  const [sources, setSources] = useState({ fields: {}, rooms: {} });
  const [draft, setDraft] = useState({ rooms: {} });
  const [saving, setSaving] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [saveError, setSaveError] = useState('');
  const pending = useRef({});
  const timer = useRef();
  const seq = useRef(0);
  const touched = useRef({ fields: new Set(), rooms: new Set() }); // values the user has typed this visit
  const autoRead = useRef(false);

  // Take the server's view of the project. Values read from the drawing fill the form, but whatever
  // the user has typed is never replaced.
  const applyModel = useCallback((m) => {
    setAnalysis(m.analysis);
    setReading(m.reading);
    setSources(m.sources);
    setDraft((d) => {
      const next = { ...m.effective, rooms: { ...(m.effective.rooms || {}) } };
      touched.current.fields.forEach((k) => { next[k] = d[k]; });
      touched.current.rooms.forEach((r) => { if (d.rooms?.[r]) next.rooms[r] = d.rooms[r]; });
      return next;
    });
  }, []);

  useEffect(() => {
    let live = true;
    setStatus({ state: 'loading' });
    autoRead.current = false;
    Promise.all([api.getProject(id), api.getModel(id)])
      .then(([p, m]) => {
        if (!live) return;
        setProject(p);
        touched.current = { fields: new Set(Object.keys(m.inputs).filter((k) => k !== 'rooms')), rooms: new Set(Object.keys(m.inputs.rooms || {})) };
        setDraft({ rooms: {}, ...m.inputs });
        applyModel(m);
        setStatus({ state: 'ready' });
      })
      .catch((error) => live && setStatus({ state: 'error', error }));
    return () => { live = false; };
  }, [id, applyModel]);

  // Inputs are sent to Flask shortly after the last keystroke. Results always come back from the server.
  const flush = useCallback(async () => {
    clearTimeout(timer.current);
    const patch = pending.current;
    if (!Object.keys(patch).length) return;
    pending.current = {};
    const mine = ++seq.current;
    setSaving(true);
    try {
      const model = await api.saveInputs(id, patch);
      if (mine === seq.current) { applyModel(model); setFieldErrors({}); setSaveError(''); }
    } catch (e) {
      if (mine === seq.current) { setFieldErrors(e.fields || {}); setSaveError(e.message); }
    } finally {
      if (mine === seq.current) setSaving(false);
    }
  }, [id, applyModel]);

  const update = useCallback((patch) => {
    for (const [k, v] of Object.entries(patch)) {
      if (k === 'rooms') {
        for (const [room, zone] of Object.entries(v)) touched.current.rooms[zone ? 'add' : 'delete'](room);
      } else {
        touched.current.fields[v !== '' && v != null ? 'add' : 'delete'](k); // clearing a field hands it back to the drawing
      }
    }
    setDraft((d) => ({ ...d, ...patch, rooms: patch.rooms ? { ...d.rooms, ...patch.rooms } : d.rooms }));
    const prev = pending.current;
    pending.current = { ...prev, ...patch };
    if (patch.rooms) pending.current.rooms = { ...prev.rooms, ...patch.rooms };
    clearTimeout(timer.current);
    timer.current = setTimeout(flush, 350);
  }, [flush]);

  useEffect(() => () => { flush(); }, [flush]);

  const readState = project?.plan?.reading;

  // Reading a drawing takes a while. Check back until it is done, then show what was found.
  useEffect(() => {
    if (readState !== 'pending') return undefined;
    let live = true;
    const tick = async () => {
      try {
        const [p, m] = await Promise.all([api.getProject(id), api.getModel(id)]);
        if (!live) return;
        setProject(p);
        applyModel(m);
      } catch { /* keep trying; a dropped request should not stop the reading */ }
    };
    tick();
    const t = setInterval(tick, 2500);
    return () => { live = false; clearInterval(t); };
  }, [readState, id, applyModel]);

  const reread = useCallback(async () => {
    try {
      const p = await api.rereadPlan(id);
      setProject(p);
    } catch (e) {
      setSaveError(e.message);
    }
  }, [id]);

  // Plans uploaded before the reader was connected are read once, automatically.
  useEffect(() => {
    if (status.state === 'ready' && readState === 'none' && !autoRead.current) {
      autoRead.current = true;
      reread();
    }
  }, [status.state, readState, reread]);

  if (status.state === 'loading') return <div className="wrap"><p className="mut">Loading project…</p></div>;
  if (status.state === 'error') {
    return (
      <div className="wrap">
        <h2>{status.error.status === 404 ? 'Project not found' : 'Could not load the project'}</h2>
        <p className="mut" style={{ margin: '10px 0 18px' }}>{status.error.message}</p>
        <Link className="btn" to="/dashboard">Back to the Dashboard</Link>
      </div>
    );
  }
  const tabs = [['', 'Project home'], ['structure', 'Structure'], ['cost', 'Cost'], ['vastu', 'Vastu']];
  return (
    <>
      <div className="subbar">
        <strong>{project.name}</strong>
        <nav className="tabs" aria-label="Project">
          {tabs.map(([path, label]) => <NavLink key={label} to={path} end>{label}</NavLink>)}
        </nav>
        <span className="saving" role="status">{saving ? 'Saving…' : saveError ? 'Not saved' : ''}</span>
      </div>
      {saveError && <p className="ferr banner" role="alert">{saveError}</p>}
      <Outlet context={{ project, setProject, draft, update, analysis, sources, reading, reread, fieldErrors }} />
    </>
  );
}
