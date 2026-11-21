import { api } from '../api.js';

export default function PlanPreview({ project, children }) {
  const plan = project.plan;
  let body;
  if (!plan) {
    body = <div className="file">No plan uploaded yet.</div>;
  } else if (['png', 'jpg', 'jpeg'].includes(plan.ext)) {
    body = <img src={api.planUrl(project.id, plan.uploaded_at)} alt={`Uploaded plan ${plan.name}`} />;
  } else if (plan.ext === 'pdf') {
    body = (
      <object className="pdf" data={api.planUrl(project.id, plan.uploaded_at)} type="application/pdf" aria-label={plan.name}>
        <div className="file">PDF preview is not available in this browser.</div>
      </object>
    );
  } else {
    body = <div className="file">{plan.ext.toUpperCase()} file: {plan.name}<br />Preview is not available in the browser.</div>;
  }
  return <div className="pl">{body}{children}</div>;
}
