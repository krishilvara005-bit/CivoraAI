import { Link, useOutletContext } from 'react-router-dom';
import { fmtSize } from '../api.js';
import DrawingReading from '../components/DrawingReading.jsx';
import PlanPreview from '../components/PlanPreview.jsx';
import UploadButton from '../components/UploadButton.jsx';
import { PageHead } from '../components/ui.jsx';

export default function ProjectHome() {
  const { project, setProject, reading, reread } = useOutletContext();
  const has = !!project.plan;
  const lock = has ? {} : { 'aria-disabled': true, tabIndex: -1, style: { opacity: 0.45, pointerEvents: 'none' } };

  return (
    <div className="wrap">
      <PageHead title={project.name} project={{ name: 'Project home' }} />
      <div className="grid2">
        <div className="card">
          <span className="k">Step 1 &bull; Plan Drawing</span>
          <h3>Plan</h3>
          <PlanPreview project={project} />
          {has && <p className="note" style={{ margin: '0 0 12px' }}>{project.plan.name} ({fmtSize(project.plan.size)})</p>}
          <UploadButton projectId={project.id} onUploaded={setProject} label={has ? 'Replace plan from computer' : 'Upload plan from computer'} />
          <p className="note" style={{ marginTop: '12px' }}>JPG, PNG, PDF, DXF or DWG. Files are stored on your server. JPG, PNG and PDF drawings are read automatically to fill in floors, size and rooms.</p>
          {has && <DrawingReading reading={reading} onReread={reread} />}
        </div>
        <div className="card">
          <span className="k">Step 2 &bull; Choose an Analyzer</span>
          <h3>Three analyzers</h3>
          <p className="mut" style={{ marginBottom: 20 }}>{has ? 'Open an analyzer for this plan.' : 'Upload a plan to unlock the analyzers.'}</p>
          <div className="acts" style={{ justifyContent: 'flex-start', flexDirection: 'column', alignItems: 'stretch', gap: '12px' }}>
            <Link className="btn" to="structure" {...lock}>Structure Plan Analyzer</Link>
            <Link className="btn ghost" to="cost" {...lock}>Cost Estimation Analyzer</Link>
            <Link className="btn ghost" to="vastu" {...lock}>Vastu Plan Analyzer</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
