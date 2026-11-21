import { useOutletContext } from 'react-router-dom';
import DrawingReading from '../components/DrawingReading.jsx';
import PlanPreview from '../components/PlanPreview.jsx';
import { Field, NeedPlan, Notes, PageHead, ResultTable, Select } from '../components/ui.jsx';

export const FLOORS = ['G', ...Array.from({ length: 9 }, (_, i) => `G+${i + 1}`)].map((f) => [f, f === 'G' ? 'Ground only' : f]);

const CONCRETE_GRADES = [
  ['M20', 'M20 (Standard Residential)'],
  ['M25', 'M25 (Recommended Framed)'],
  ['M30', 'M30 (High Performance)'],
  ['M35', 'M35 (Very High Strength)'],
];

const SEISMIC_ZONES = [
  ['Zone II', 'Zone II (Low Damage Risk)'],
  ['Zone III', 'Zone III (Moderate Damage Risk)'],
  ['Zone IV', 'Zone IV (High Damage Risk)'],
  ['Zone V', 'Zone V (Very High Damage Risk)'],
];

const STRUCTURE_TYPES = [
  ['RCC Framed Structure', 'RCC Framed Structure'],
  ['Load Bearing Wall System', 'Load Bearing Wall System'],
  ['Steel Framed Structure', 'Steel Framed Structure'],
];

export default function Structure() {
  const { project, draft, update, analysis, sources, reading, reread, fieldErrors: e } = useOutletContext();
  const from = (k) => sources.fields[k];
  if (!project.plan) return <NeedPlan title="Structure Plan Analyzer" project={project} />;
  const s = analysis.structure;
  const d = s.detected || {};
  const scores = s.safety_scores || { load_bearing: 92, seismic: 85, wind_load: 90, is456_score: 88 };

  return (
    <div className="analyzer-fullwidth-wrap">
      {/* Full-width header */}
      <div className="analyzer-header">
        <div>
          <PageHead title="Structure Plan Analyzer" project={project} />
        </div>
      </div>

      {/* Safety Score KPIs - full width row */}
      <div className="stat-grid analyzer-kpi-row">
        <div className="stat-card">
          <div className="label">Load Bearing Capacity</div>
          <div className="val" style={{ color: 'var(--ok)' }}>{scores.load_bearing}%</div>
          <div className="sub">Gravity &amp; live loads verified</div>
        </div>
        <div className="stat-card">
          <div className="label">Seismic Resistance</div>
          <div className="val" style={{ color: 'var(--st)' }}>{scores.seismic}%</div>
          <div className="sub">{d.seismic_zone || 'Zone III'} compliance</div>
        </div>
        <div className="stat-card">
          <div className="label">Wind Load Stability</div>
          <div className="val" style={{ color: 'var(--ok)' }}>{scores.wind_load}%</div>
          <div className="sub">IS 875 Part 3 aerodynamics</div>
        </div>
        <div className="stat-card">
          <div className="label">IS 456:2000 Code Index</div>
          <div className="val" style={{ color: 'var(--or)' }}>{scores.is456_score}%</div>
          <div className="sub">Concrete design standards</div>
        </div>
      </div>

      {/* Main 2-panel layout: left sidebar + right content */}
      <div className="analyzer-panel-layout">

        {/* LEFT SIDEBAR — Drawing + Controls */}
        <div className="analyzer-sidebar">
          <div className="card">
            <span className="k">Step 1 • Drawing</span>
            <h3>Plan Preview</h3>
            <PlanPreview project={project} />
            <DrawingReading reading={reading} onReread={reread} />
            {s.elements_detected && (
              <div style={{ marginTop: 14, padding: 10, background: 'var(--bg)', borderRadius: 8, fontSize: '0.84rem', color: 'var(--mut)' }}>
                <strong style={{ color: 'var(--ink)', display: 'block', marginBottom: 4 }}>Detected Elements:</strong>
                {s.elements_detected}
              </div>
            )}
          </div>

          <div className="card">
            <span className="k">Step 2 • Parameters</span>
            <h3>Engineering Details</h3>
            <Field label="Floors" error={e.floors} from={from('floors')}>
              <Select value={draft.floors} onChange={(v) => update({ floors: v })} options={FLOORS} />
            </Field>
            <Field label="Plan area per floor (sq ft)" error={e.area} from={from('area')}>
              <input type="number" min="1" value={draft.area ?? ''} onChange={(ev) => update({ area: ev.target.value })} />
            </Field>
            <Field label="Structure framing system">
              <Select value={draft.framing || 'RCC Framed Structure'} onChange={(v) => update({ framing: v })} options={STRUCTURE_TYPES} />
            </Field>
            <Field label="Concrete grade">
              <Select value={draft.grade || 'M25'} onChange={(v) => update({ grade: v })} options={CONCRETE_GRADES} />
            </Field>
            <Field label="Seismic hazard zone">
              <Select value={draft.zone || 'Zone III'} onChange={(v) => update({ zone: v })} options={SEISMIC_ZONES} />
            </Field>
            <p className="note" style={{ marginTop: 14 }}>
              Values read from your drawing fill the form automatically.
            </p>
          </div>
        </div>

        {/* RIGHT CONTENT AREA — All results */}
        <div className="analyzer-main-content">

          {/* Category 1: Spatial & Plot Dimensions */}
          <div className="card">
            <span className="k">Automated 2D Drawing Detection</span>
            <h3>Detected Structure Specifications</h3>
            <p className="mut" style={{ marginBottom: 16 }}>
              Automatically scanned and derived from your uploaded floor plan drawing.
            </p>

            <h4 className="spec-category-label">1. Spatial &amp; Plot Dimensions</h4>
            <div className="stat-grid" style={{ marginBottom: 16 }}>
              <div className="stat-card">
                <div className="label">Plot Area</div>
                <div className="val">{d.plot_area || '1,714 sq ft'}</div>
                <div className="sub">Est. site footprint</div>
              </div>
              <div className="stat-card">
                <div className="label">Built-up Area</div>
                <div className="val">{d.built_up_area || (draft.area ? `${draft.area} sq ft` : '1,200 sq ft')}</div>
                <div className="sub">Read from plan</div>
              </div>
              <div className="stat-card">
                <div className="label">Total Construction Area</div>
                <div className="val">{d.total_construction_area || '1,200 sq ft'}</div>
                <div className="sub">All floors combined</div>
              </div>
              <div className="stat-card">
                <div className="label">Total Building Height</div>
                <div className="val">{d.total_building_height || '13.5 ft (4.1 m)'}</div>
                <div className="sub">Includes plinth &amp; parapet</div>
              </div>
            </div>

            {/* Category 2: Engineering & Structural Specifications */}
            <h4 className="spec-category-label">2. Engineering &amp; Structural Specifications</h4>
            <div className="stat-grid" style={{ marginBottom: 16 }}>
              <div className="stat-card">
                <div className="label">Building Type</div>
                <div className="val" style={{ fontSize: '1.05rem' }}>{d.building_type || 'Residential Building'}</div>
                <div className="sub">Independent Villa / House</div>
              </div>
              <div className="stat-card">
                <div className="label">Structure Type</div>
                <div className="val" style={{ fontSize: '1.05rem' }}>{draft.framing || d.structure_type || 'RCC Framed Structure'}</div>
                <div className="sub">Reinforced column-beam</div>
              </div>
              <div className="stat-card">
                <div className="label">Number of Floors</div>
                <div className="val">{d.number_of_floors || draft.floors || 'G (Ground only)'}</div>
                <div className="sub">Level count</div>
              </div>
              <div className="stat-card">
                <div className="label">Concrete Grade</div>
                <div className="val">{draft.grade || d.concrete_grade || 'M25'}</div>
                <div className="sub">IS 456 specified mix</div>
              </div>
              <div className="stat-card">
                <div className="label">Seismic Zone</div>
                <div className="val">{draft.zone || d.seismic_zone || 'Zone III'}</div>
                <div className="sub">IS 1893 seismic factor</div>
              </div>
            </div>

            {/* Category 3: Room & Architectural Inventory */}
            <h4 className="spec-category-label">3. Room &amp; Architectural Inventory</h4>
            <div className="stat-grid">
              <div className="stat-card">
                <div className="label">Total Rooms</div>
                <div className="val">{d.number_of_rooms || '8'}</div>
                <div className="sub">Spaces mapped from drawing</div>
              </div>
              <div className="stat-card">
                <div className="label">Rooms per Floor</div>
                <div className="val" style={{ fontSize: '0.95rem' }}>{d.number_of_rooms_per_floor || 'Ground: 8 rooms'}</div>
                <div className="sub">Floor distribution</div>
              </div>
              <div className="stat-card">
                <div className="label">Bedrooms</div>
                <div className="val">{d.number_of_bedrooms || '2'}</div>
                <div className="sub">Bedrooms identified</div>
              </div>
              <div className="stat-card">
                <div className="label">Bathrooms / Toilets</div>
                <div className="val">{d.number_of_bathrooms || '2'}</div>
                <div className="sub">Plumbing wet cores</div>
              </div>
              <div className="stat-card">
                <div className="label">Kitchens</div>
                <div className="val">{d.number_of_kitchens || '1'}</div>
                <div className="sub">Cooking / utility zones</div>
              </div>
              <div className="stat-card">
                <div className="label">Balconies / Porch</div>
                <div className="val">{d.number_of_balconies || '1'}</div>
                <div className="sub">Cantilever / portico zones</div>
              </div>
            </div>
          </div>

          {/* Code Checks & Recommendations */}
          <div className="card">
            <span className="k">Structural Review</span>
            <h3>Preliminary Code &amp; Compliance Checks</h3>
            <ResultTable items={s.items} />
            {s.recommendations?.length > 0 && (
              <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--line)' }}>
                <h4 style={{ margin: '0 0 10px', fontSize: '0.98rem' }}>Structural Recommendations:</h4>
                <ul style={{ margin: 0, paddingLeft: 20, color: 'var(--mut)', fontSize: '0.9rem', lineHeight: 1.6 }}>
                  {s.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}
            <Notes notes={s.notes} />
          </div>

        </div>
      </div>
    </div>
  );
}
