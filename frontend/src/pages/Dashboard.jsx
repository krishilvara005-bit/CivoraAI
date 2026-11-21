import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api.js';
import UploadButton from '../components/UploadButton.jsx';

function NewProject({ open, onClose, onCreate }) {
  const dlg = useRef(null);
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  useEffect(() => {
    if (open && !dlg.current.open) dlg.current.showModal();
    if (!open && dlg.current.open) dlg.current.close();
  }, [open]);

  async function submit(e) {
    e.preventDefault();
    setError('');
    try {
      await onCreate(name.trim());
      setName('');
    } catch (err) {
      setError(err.message);
    }
  }
  return (
    <dialog ref={dlg} onClose={onClose} aria-labelledby="np-t">
      <form onSubmit={submit}>
        <h3 id="np-t">Create a project</h3>
        <label>Project name
          <input value={name} onChange={(e) => setName(e.target.value)} maxLength={60} required autoFocus placeholder="For example, Patel Residence" />
        </label>
        {error && <p className="ferr" role="alert">{error}</p>}
        <div className="acts">
          <button type="button" className="btn ghost" onClick={onClose}>Cancel</button>
          <button className="btn">Create project</button>
        </div>
      </form>
    </dialog>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState(null);
  const [error, setError] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => { api.listProjects().then(setProjects).catch((e) => setError(e.message)); }, []);

  async function create(name) {
    const p = await api.createProject(name);
    navigate(`/projects/${p.id}`);
  }
  async function remove(p) {
    if (!window.confirm(`Delete "${p.name}" and its plan?`)) return;
    try {
      await api.deleteProject(p.id);
      setProjects((list) => list.filter((x) => x.id !== p.id));
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="wrap">
      <div className="row">
        <div><h2>Dashboard</h2><p className="mut">Your projects</p></div>
        <button className="btn" onClick={() => setCreating(true)}>Create project</button>
      </div>
      {error && <p className="ferr" role="alert">{error}</p>}
      {projects === null && !error && <p className="mut">Loading projects…</p>}
      {projects?.length === 0 && <div className="empty"><h3>No projects yet</h3><p>Create your first project to start.</p></div>}
      {projects?.length > 0 && (
        <div className="grid2">
          {projects.map((p) => (
            <div className="card" key={p.id}>
              <h3>{p.name}</h3>
              <p className="mut">{p.plan ? `Plan: ${p.plan.name}` : 'No plan uploaded yet'}</p>
              <div className="acts" style={{ justifyContent: 'flex-start', flexWrap: 'wrap' }}>
                <Link className="btn sm" to={`/projects/${p.id}`}>Open project</Link>
                <UploadButton projectId={p.id} className="btn sm ghost" onUploaded={() => navigate(`/projects/${p.id}`)} />
                <button className="btn sm ghost" onClick={() => remove(p)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
      <NewProject open={creating} onClose={() => setCreating(false)} onCreate={create} />
    </div>
  );
}
