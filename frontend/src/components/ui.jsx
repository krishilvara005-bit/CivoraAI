import { Link } from 'react-router-dom';

const STATUS = {
  provided: 'ok', not_provided: 'nt', not_evaluated: 'wn',
  matches: 'ok', acceptable: 'wn', avoid: 'bad', needs_north: 'wn', found_needs_north: 'wn', not_selected: 'nt',
};
export const statusClass = (s) => STATUS[s] || 'nt';

export function Field({ label, error, from, children }) {
  return (
    <label>
      <span>{label}{from === 'drawing' && <span className="src">read from drawing</span>}</span>
      {children}
      {error && <span className="ferr" role="alert">{error}</span>}
    </label>
  );
}

export function Select({ value, onChange, options, ...rest }) {
  return (
    <select value={value ?? ''} onChange={(e) => onChange(e.target.value)} {...rest}>
      <option value="">Select</option>
      {options.map(([v, text]) => <option key={v} value={v}>{text}</option>)}
    </select>
  );
}

export function ResultTable({ items }) {
  return (
    <table>
      <tbody>
        {items.map((i) => (
          <tr key={i.key}>
            <td>{i.label}</td>
            <td className={statusClass(i.status)}>{i.display}{i.source === 'drawing' && <span className="src">from drawing</span>}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export const Notes = ({ notes }) => notes?.map((n) => <p className="note" key={n}>{n}</p>);

export function PageHead({ title, project }) {
  return (
    <div className="row"><div><h2>{title}</h2><p className="mut">{project.name}</p></div></div>
  );
}

export function NeedPlan({ title, project }) {
  return (
    <div className="wrap">
      <PageHead title={title} project={project} />
      <div className="empty">
        <h3>Upload a plan first</h3>
        <p style={{ marginBottom: 16 }}>This analyzer works on the plan you add to the project.</p>
        <Link className="btn" to={`/projects/${project.id}`}>Go to Project home</Link>
      </div>
    </div>
  );
}
