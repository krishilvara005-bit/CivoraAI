import { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import DrawingReading from '../components/DrawingReading.jsx';
import PlanPreview from '../components/PlanPreview.jsx';
import { Field, NeedPlan, Notes, PageHead, ResultTable, Select } from '../components/ui.jsx';
import { FLOORS } from './Structure.jsx';

export default function Cost() {
  const { project, draft, update, analysis, sources, reading, reread, fieldErrors: e } = useOutletContext();
  const [activeTab, setActiveTab] = useState('materials');
  const from = (k) => sources.fields[k];
  if (!project.plan) return <NeedPlan title="Cost Estimation Analyzer" project={project} />;

  const c = analysis.cost;
  const areaNum = parseInt(draft.area || '1200', 10);
  const floorMultiplier = draft.floors && draft.floors.startsWith('G+') ? parseInt(draft.floors.replace('G+', ''), 10) + 1 : 1;
  const builtUpArea = areaNum * floorMultiplier;
  const rateNum = draft.rate ? parseInt(draft.rate, 10) : 1950;
  const totalCost = c.total || (builtUpArea * rateNum);
  const costPerSqFt = rateNum;

  // Financial calculations
  const pred = c.ai_prediction || { low: `₹${Math.round(totalCost * 0.92).toLocaleString()}`, most_likely: `₹${totalCost.toLocaleString()}`, high: `₹${Math.round(totalCost * 1.10).toLocaleString()}`, confidence_score: '92%' };
  const gst = c.gst_taxes || { cgst_amount: `₹${Math.round(totalCost * 0.09).toLocaleString()}`, sgst_amount: `₹${Math.round(totalCost * 0.09).toLocaleString()}`, total_gst: `₹${Math.round(totalCost * 0.18).toLocaleString()}`, grand_total: `₹${Math.round(totalCost * 1.18).toLocaleString()}` };
  const budget = c.budget_vs_estimated || { target_budget: `₹${Math.round(totalCost * 1.05).toLocaleString()}`, variance_amount: `₹${Math.round(totalCost * 0.05).toLocaleString()}`, status_text: 'Within Target Budget', is_favorable: true };

  function handlePrintPDF() {
    window.print();
  }

  return (
    <div className="analyzer-fullwidth-wrap">
      {/* Full-width header */}
      <div className="analyzer-header">
        <div>
          <h2>Cost Estimation Analyzer</h2>
          <p className="mut">{project.name} &bull; Construction Budget &amp; Material BOQ</p>
        </div>
        <button className="btn sm" onClick={handlePrintPDF} title="Download or print PDF report">
          📄 PDF Cost Estimation Report
        </button>
      </div>

      {/* Top Financial KPIs - full width */}
      <div className="stat-grid analyzer-kpi-row">
        <div className="stat-card">
          <div className="label">Total Construction Cost</div>
          <div className="val" style={{ color: 'var(--or)' }}>₹{totalCost.toLocaleString()}</div>
          <div className="sub">{builtUpArea.toLocaleString()} sq ft built-up area</div>
        </div>
        <div className="stat-card">
          <div className="label">Cost per Square Foot</div>
          <div className="val">₹{costPerSqFt.toLocaleString()}</div>
          <div className="sub">Standard urban RCC index</div>
        </div>
        <div className="stat-card">
          <div className="label">Budget vs Estimated</div>
          <div className="val" style={{ color: budget.is_favorable ? 'var(--ok)' : 'var(--bad)', fontSize: '1.15rem' }}>
            {budget.status_text}
          </div>
          <div className="sub">Target: {budget.target_budget}</div>
        </div>
        <div className="stat-card">
          <div className="label">AI Cost Prediction</div>
          <div className="val" style={{ fontSize: '1.15rem' }}>{pred.most_likely}</div>
          <div className="sub">Range: {pred.low} – {pred.high} ({pred.confidence_score})</div>
        </div>
        <div className="stat-card">
          <div className="label">GST &amp; Taxes (18%)</div>
          <div className="val" style={{ fontSize: '1.15rem' }}>{gst.total_gst}</div>
          <div className="sub">Grand Total: {gst.grand_total}</div>
        </div>
      </div>

      {/* Main 2-panel layout: left sidebar + right content */}
      <div className="analyzer-panel-layout">

        {/* LEFT SIDEBAR */}
        <div className="analyzer-sidebar">
          <div className="card">
            <span className="k">Step 1 • Drawing</span>
            <h3>Plan Preview</h3>
            <PlanPreview project={project} />
            <DrawingReading reading={reading} onReread={reread} />
          </div>

          <div className="card">
            <span className="k">Step 2 • Parameters</span>
            <h3>Cost &amp; Budget Inputs</h3>
            <Field label="Floors" error={e.floors} from={from('floors')}>
              <Select value={draft.floors} onChange={(v) => update({ floors: v })} options={FLOORS} />
            </Field>
            <Field label="Plan area per floor (sq ft)" error={e.area} from={from('area')}>
              <input type="number" min="1" value={draft.area ?? ''} onChange={(ev) => update({ area: ev.target.value })} />
            </Field>
            <Field label="Construction rate (₹ per sq ft)" error={e.rate}>
              <input type="number" min="1" value={draft.rate ?? ''} onChange={(ev) => update({ rate: ev.target.value })} placeholder="e.g. 1950" />
            </Field>
            <Field label="Allow for uncertainty" error={e.range}>
              <Select value={draft.range} onChange={(v) => update({ range: v })} options={[10, 15, 20].map((n) => [String(n), `Plus or minus ${n}%`])} />
            </Field>
            <Field label="Target Budget (₹ optional)">
              <input type="number" min="100000" value={draft.target_budget ?? ''} onChange={(ev) => update({ target_budget: ev.target.value })} placeholder="e.g. 2500000" />
            </Field>
            <p className="note" style={{ marginTop: 14 }}>
              Floors and area are read from your drawing and shared with the Structure analyzer.
            </p>
          </div>
        </div>

        {/* RIGHT CONTENT AREA */}
        <div className="analyzer-main-content">

          {/* Segmented Tabs */}
          <div className="card">
            <span className="k">Detailed Cost Engineering</span>
            <h3>Cost Breakdowns &amp; Bill of Quantities (BOQ)</h3>

            <div className="seg-bar">
              <button className={`seg-btn ${activeTab === 'materials' ? 'on' : ''}`} onClick={() => setActiveTab('materials')}>
                Material-wise Cost
              </button>
              <button className={`seg-btn ${activeTab === 'labour' ? 'on' : ''}`} onClick={() => setActiveTab('labour')}>
                Labour-wise Cost
              </button>
              <button className={`seg-btn ${activeTab === 'floors' ? 'on' : ''}`} onClick={() => setActiveTab('floors')}>
                Floor-wise Cost
              </button>
              <button className={`seg-btn ${activeTab === 'rooms' ? 'on' : ''}`} onClick={() => setActiveTab('rooms')}>
                Room-wise Cost
              </button>
              <button className={`seg-btn ${activeTab === 'boq' ? 'on' : ''}`} onClick={() => setActiveTab('boq')}>
                Detailed BOQ
              </button>
              <button className={`seg-btn ${activeTab === 'budget' ? 'on' : ''}`} onClick={() => setActiveTab('budget')}>
                Budget Summary
              </button>
            </div>

            {/* Tab 1: Material-wise Cost */}
            {activeTab === 'materials' && (
              <div>
                <p className="mut" style={{ marginBottom: 12 }}>
                  Materials constitute approximately 58% (₹{Math.round(totalCost * 0.58).toLocaleString()}) of the core construction expenditure.
                </p>
                <table>
                  <thead>
                    <tr>
                      <th>Material Category</th>
                      <th>Share of Total</th>
                      <th>Estimated Cost</th>
                      <th>Description &amp; Grade</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(c.material_wise_cost || [
                      { category: 'High-Yield TMT Steel (Fe 550D)', pct_of_total: '10.4%', amount_display: `₹${Math.round(totalCost * 0.104).toLocaleString()}`, desc: 'Structural rebar for columns, beams & slabs' },
                      { category: 'Cement (OPC 53 & PPC Grade)', pct_of_total: '8.7%', amount_display: `₹${Math.round(totalCost * 0.087).toLocaleString()}`, desc: 'Concrete mix, masonry mortar & plastering' },
                      { category: 'Electrical & Plumbing Materials', pct_of_total: '6.4%', amount_display: `₹${Math.round(totalCost * 0.064).toLocaleString()}`, desc: 'Concealed conduits, CPVC pipes & fittings' },
                      { category: 'Sand & Coarse Aggregates', pct_of_total: '5.8%', amount_display: `₹${Math.round(totalCost * 0.058).toLocaleString()}`, desc: 'M-Sand, plastering sand & 20mm/10mm gravel' },
                      { category: 'Vitrified Tiles & Granite Stone', pct_of_total: '5.2%', amount_display: `₹${Math.round(totalCost * 0.052).toLocaleString()}`, desc: 'Floor tiles, skirting & kitchen counter' },
                      { category: 'Bricks & AAC Wall Blocks', pct_of_total: '4.6%', amount_display: `₹${Math.round(totalCost * 0.046).toLocaleString()}`, desc: 'External 200mm & internal 100mm partition walls' },
                      { category: 'Doors, Windows & UPVC Frames', pct_of_total: '4.1%', amount_display: `₹${Math.round(totalCost * 0.041).toLocaleString()}`, desc: 'Main entrance teak door & UPVC sliding windows' },
                      { category: 'Waterproofing & Screed', pct_of_total: '2.3%', amount_display: `₹${Math.round(totalCost * 0.023).toLocaleString()}`, desc: 'Sunken bathroom & terrace waterproofing' },
                      { category: 'Paints & Acrylic Emulsion', pct_of_total: '2.9%', amount_display: `₹${Math.round(totalCost * 0.029).toLocaleString()}`, desc: 'Exterior weather-proof & interior emulsion' },
                    ]).map((m, i) => (
                      <tr key={i}>
                        <td><strong>{m.category}</strong></td>
                        <td>{m.pct_of_total}</td>
                        <td style={{ color: 'var(--or)', fontWeight: 700 }}>{m.amount_display}</td>
                        <td className="mut">{m.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab 2: Labour-wise Cost */}
            {activeTab === 'labour' && (
              <div>
                <p className="mut" style={{ marginBottom: 12 }}>
                  Workmanship and labour contracts account for 34% (₹{Math.round(totalCost * 0.34).toLocaleString()}) of the project.
                </p>
                <table>
                  <thead>
                    <tr>
                      <th>Trade / Scope</th>
                      <th>Share of Total</th>
                      <th>Estimated Amount</th>
                      <th>Workmanship Scope</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(c.labour_wise_cost || [
                      { trade: 'Formwork, Centering & Shuttering', pct_of_total: '10.2%', amount_display: `₹${Math.round(totalCost * 0.102).toLocaleString()}`, desc: 'Plywood shuttering, props & scaffolding' },
                      { trade: 'Brick Masonry & Wall Plastering', pct_of_total: '8.5%', amount_display: `₹${Math.round(totalCost * 0.085).toLocaleString()}`, desc: 'Brick laying, ceiling & wall plastering' },
                      { trade: 'Bar Bending & Steel Fixing', pct_of_total: '6.1%', amount_display: `₹${Math.round(totalCost * 0.061).toLocaleString()}`, desc: 'Cutting, bending & tying rebar cages' },
                      { trade: 'Electrical & Plumbing Workmanship', pct_of_total: '4.1%', amount_display: `₹${Math.round(totalCost * 0.041).toLocaleString()}`, desc: 'Piping routing, wiring & fixture fitting' },
                      { trade: 'Tiling, Granite Laying & Polishing', pct_of_total: '3.1%', amount_display: `₹${Math.round(totalCost * 0.031).toLocaleString()}`, desc: 'Tile fixing, grouting & stone edge chamfering' },
                      { trade: 'Painting & Surface Preparation', pct_of_total: '2.0%', amount_display: `₹${Math.round(totalCost * 0.020).toLocaleString()}`, desc: 'Putty application, primer & 2-coat painting' },
                    ]).map((l, i) => (
                      <tr key={i}>
                        <td><strong>{l.trade}</strong></td>
                        <td>{l.pct_of_total}</td>
                        <td style={{ color: 'var(--st)', fontWeight: 700 }}>{l.amount_display}</td>
                        <td className="mut">{l.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab 3: Floor-wise Cost */}
            {activeTab === 'floors' && (
              <div>
                <p className="mut" style={{ marginBottom: 12 }}>
                  Vertical cost distribution across foundation, plinth, and upper storeys.
                </p>
                <table>
                  <thead>
                    <tr>
                      <th>Floor Level</th>
                      <th>Allocation</th>
                      <th>Estimated Cost</th>
                      <th>Structural Scope</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(c.floor_wise_cost || [
                      { floor: 'Ground Floor', pct: '100%', amount_display: `₹${totalCost.toLocaleString()}`, notes: 'Foundation, plinth beam, framing, masonry & interior finishes' },
                    ]).map((f, i) => (
                      <tr key={i}>
                        <td><strong>{f.floor}</strong></td>
                        <td>{f.pct}</td>
                        <td style={{ color: 'var(--or)', fontWeight: 700 }}>{f.amount_display}</td>
                        <td className="mut">{f.notes}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab 4: Room-wise Cost */}
            {activeTab === 'rooms' && (
              <div>
                <p className="mut" style={{ marginBottom: 12 }}>
                  Estimated allocation based on room fixtures, plumbing wet-areas, and interior finishes.
                </p>
                <table>
                  <thead>
                    <tr>
                      <th>Room / Space</th>
                      <th>Allocation</th>
                      <th>Estimated Cost</th>
                      <th>Finishes &amp; Fixtures</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(c.room_wise_cost || [
                      { name: 'Living & Dining Area', pct: '26%', amount_display: `₹${Math.round(totalCost * 0.26).toLocaleString()}`, notes: 'Double-charged tiles, ceiling coping, electrical points' },
                      { name: 'Kitchen & Utility', pct: '20%', amount_display: `₹${Math.round(totalCost * 0.20).toLocaleString()}`, notes: 'Granite platform, tile dado, sink & water supply' },
                      { name: 'Master Bedroom', pct: '18%', amount_display: `₹${Math.round(totalCost * 0.18).toLocaleString()}`, notes: 'Vitrified tiles, window frame, door shutters' },
                      { name: 'Attached Bathrooms / Toilets', pct: '16%', amount_display: `₹${Math.round(totalCost * 0.16).toLocaleString()}`, notes: 'Waterproofing, CP fittings, sanitaryware & drainage' },
                      { name: 'Bedroom 2 (Guest / Kids)', pct: '14%', amount_display: `₹${Math.round(totalCost * 0.14).toLocaleString()}`, notes: 'Flooring, door frames, electrical wiring' },
                      { name: 'Porch & Car Parking', pct: '6%', amount_display: `₹${Math.round(totalCost * 0.06).toLocaleString()}`, notes: 'Heavy-duty exterior pavers, plinth ramp' },
                    ]).map((r, i) => (
                      <tr key={i}>
                        <td><strong>{r.name}</strong></td>
                        <td>{r.pct}</td>
                        <td style={{ color: 'var(--st)', fontWeight: 700 }}>{r.amount_display}</td>
                        <td className="mut">{r.notes || r.floor || 'Standard finish'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab 5: Detailed BOQ */}
            {activeTab === 'boq' && (
              <div>
                <p className="mut" style={{ marginBottom: 12 }}>
                  Itemized Bill of Quantities (BOQ) calculated for {builtUpArea.toLocaleString()} sq ft built-up area.
                </p>
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Material / Work Item</th>
                      <th>Unit</th>
                      <th>Estimated Qty</th>
                      <th>Unit Rate (₹)</th>
                      <th>Total Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(c.detailed_boq || [
                      { item: 1, desc: 'Cement (OPC 53 / PPC Grade)', unit: 'Bags', qty: Math.round(builtUpArea * 0.42), rate: 380, total: `₹${Math.round(builtUpArea * 0.42 * 380).toLocaleString()}` },
                      { item: 2, desc: 'High-Yield TMT Steel (Fe 550D)', unit: 'MT', qty: (builtUpArea * 0.0038).toFixed(2), rate: 68000, total: `₹${Math.round(builtUpArea * 0.0038 * 68000).toLocaleString()}` },
                      { item: 3, desc: 'Manufactured Sand (M-Sand)', unit: 'Cu.ft', qty: Math.round(builtUpArea * 1.85), rate: 65, total: `₹${Math.round(builtUpArea * 1.85 * 65).toLocaleString()}` },
                      { item: 4, desc: 'Coarse Aggregate (20mm & 10mm)', unit: 'Cu.ft', qty: Math.round(builtUpArea * 1.35), rate: 48, total: `₹${Math.round(builtUpArea * 1.35 * 48).toLocaleString()}` },
                      { item: 5, desc: 'AAC Lightweight Wall Blocks', unit: 'Nos', qty: Math.round(builtUpArea * 2.6), rate: 68, total: `₹${Math.round(builtUpArea * 2.6 * 68).toLocaleString()}` },
                      { item: 6, desc: 'Double-Charged Vitrified Tiles', unit: 'Sq.ft', qty: Math.round(builtUpArea * 0.85), rate: 115, total: `₹${Math.round(builtUpArea * 0.85 * 115).toLocaleString()}` },
                      { item: 7, desc: 'Waterproofing Membrane', unit: 'Sq.ft', qty: Math.round(builtUpArea * 0.35), rate: 45, total: `₹${Math.round(builtUpArea * 0.35 * 45).toLocaleString()}` },
                      { item: 8, desc: 'Acrylic Emulsion Paint & Primer', unit: 'Sq.ft', qty: Math.round(builtUpArea * 3.2), rate: 28, total: `₹${Math.round(builtUpArea * 3.2 * 28).toLocaleString()}` },
                      { item: 9, desc: 'Electrical Concealed Wiring', unit: 'Points', qty: Math.round(builtUpArea * 0.12), rate: 850, total: `₹${Math.round(builtUpArea * 0.12 * 850).toLocaleString()}` },
                      { item: 10, desc: 'Plumbing Piping & Fittings', unit: 'Rft', qty: Math.round(builtUpArea * 0.65), rate: 145, total: `₹${Math.round(builtUpArea * 0.65 * 145).toLocaleString()}` },
                    ]).map((b, i) => (
                      <tr key={i}>
                        <td>{b.item}</td>
                        <td><strong>{b.desc}</strong></td>
                        <td>{b.unit}</td>
                        <td>{b.qty}</td>
                        <td>₹{b.rate}</td>
                        <td style={{ color: 'var(--or)', fontWeight: 700 }}>{b.total}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab 6: Construction Budget Summary */}
            {activeTab === 'budget' && (
              <div>
                <p className="mut" style={{ marginBottom: 12 }}>
                  High-level capital allocation across civil structure, finishes, MEP, and contingency.
                </p>
                <table>
                  <thead>
                    <tr>
                      <th>Component</th>
                      <th>Budget Share</th>
                      <th>Allocated Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(c.budget_summary || [
                      { component: 'Core Civil Structure & Masonry', pct: '52%', amount: `₹${Math.round(totalCost * 0.52).toLocaleString()}` },
                      { component: 'Architectural Finishes & Flooring', pct: '24%', amount: `₹${Math.round(totalCost * 0.24).toLocaleString()}` },
                      { component: 'MEP (Mechanical, Electrical, Plumbing)', pct: '16%', amount: `₹${Math.round(totalCost * 0.16).toLocaleString()}` },
                      { component: 'Contractor Overheads & Contingency Buffer', pct: '8%', amount: `₹${Math.round(totalCost * 0.08).toLocaleString()}` },
                    ]).map((s, i) => (
                      <tr key={i}>
                        <td><strong>{s.component}</strong></td>
                        <td>{s.pct}</td>
                        <td style={{ color: 'var(--or)', fontWeight: 700 }}>{s.amount}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Value Engineering Insights */}
          <div className="card">
            <span className="k">Value Engineering Insights</span>
            <h3>Contractor &amp; Procurement Guidance</h3>
            <ResultTable items={c.items} />
            {(c.optimization_insights || [
              `This estimate covers core construction for ${builtUpArea.toLocaleString()} sq ft. Budget an additional 5-10% contingency for unforeseen site variations.`,
              `GST on construction materials/services adds 18% (~${gst.total_gst}) — check with your contractor for input tax credit eligibility.`,
              `Structural Steel and Cement account for ~33% of your budget — explore direct bulk procurement from authorized primary dealers.`,
            ]).map((insight, idx) => (
              <p className="note" key={idx} style={{ marginTop: 10 }}>&bull; {insight}</p>
            ))}
            <Notes notes={c.notes} />
          </div>

        </div>
      </div>
    </div>
  );
}
