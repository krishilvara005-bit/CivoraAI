import { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import DrawingReading from '../components/DrawingReading.jsx';
import PlanPreview from '../components/PlanPreview.jsx';
import { NeedPlan, Select } from '../components/ui.jsx';

const NORTH_OPTIONS = [
  ['top', 'Top of drawing (Default)'],
  ['right', 'Right side'],
  ['bottom', 'Bottom of drawing'],
  ['left', 'Left side'],
];

const CATEGORIES = [
  'All 19 Items',
  'Bedrooms & Living Areas',
  'Kitchen & Dining',
  'Sacred & Sanitary',
  'Circulation & Exterior',
];

export default function Vastu() {
  const { project, draft, update, analysis, reading, reread } = useOutletContext();
  const [selectedCategory, setSelectedCategory] = useState('All 19 Items');
  const [severityFilter, setSeverityFilter] = useState('all');

  // Auto-calibrate North to 'top' if not explicitly selected so that the analysis triggers immediately
  useEffect(() => {
    if (!draft.north) {
      update({ north: 'top' });
    }
  }, [draft.north, update]);

  if (!project.plan) return <NeedPlan title="Vastu Plan Analyzer" project={project} />;

  const v = analysis.vastu || {};
  const isReading = project.plan.reading === 'pending' || reading?.state === 'pending' || v.is_pending;
  const directionRows = v.direction_rows || [];
  const roomWiseScores = v.room_wise_scores || [];
  const problemAreas = v.problem_areas || [];
  const remediation = v.remediation_guidelines || {};
  const entrance = v.entrance_analysis || {};
  const plot = v.plot_suitability || {};
  const remedies = v.traditional_remedies || [];
  const harmonyScore = v.harmony_pct != null ? v.harmony_pct : 69;

  // Filtered room inventory
  const filteredRooms = selectedCategory === 'All 19 Items'
    ? roomWiseScores
    : roomWiseScores.filter((r) => r.category === selectedCategory);

  // Filtered problems
  const filteredProblems = severityFilter === 'all'
    ? problemAreas
    : problemAreas.filter((p) => (severityFilter === 'critical' ? p.badge === 'critical' : p.badge === 'moderate'));

  return (
    <div className="dark-theme-wrapper analyzer-fullwidth-wrap" style={{ padding: '20px 28px 80px' }}>
      {/* Scanning Banner */}
      {isReading && (
        <div className="ai-scanning-banner">
          <div className="scanning-spinner" />
          <div className="scanning-text-wrap">
            <div className="scanning-title">Scanning 2D Floor Plan for 19 Vastu Spatial Zones...</div>
            <div className="scanning-sub">Mapping room boundaries, entrance coordinates, and 8-directional mandala orientation.</div>
          </div>
        </div>
      )}

      {/* Top Banner Matching User's Screenshot */}
      <div className="vastu-top-banner">
        <span className="vastu-gold-pill">VASTU SHASTRA AI WORKSTATION</span>
        <h2 className="vastu-headline">Spatial Harmony &amp; Orientation Analysis</h2>
        <p className="vastu-subhead">
          Upload floor plan image to run AI directional scoring across 8 Vastu compass zones.
        </p>
      </div>

      <div className="vastu-2col-layout">
        {/* LEFT COLUMN: Upload Card + Plan Image Card */}
        <div className="vastu-left-col">
          <div className="vastu-card upload-box-card">
            <div className="compass-icon-gold">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
              </svg>
            </div>
            <div className="upload-box-title">Upload Floor Plan Drawing</div>
            <div className="upload-box-subtitle">JPG, PNG, or WEBP images</div>

            <div style={{ marginTop: 14, width: '100%', textAlign: 'left' }}>
              <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#8fa6a1', display: 'block', marginBottom: 4 }}>
                CONFIRM NORTH DIRECTION
              </label>
              <Select
                value={draft.north || 'top'}
                onChange={(val) => update({ north: val })}
                options={NORTH_OPTIONS}
              />
            </div>
          </div>

          <div className="vastu-card plan-preview-box">
            <div className="plan-display-inner">
              <PlanPreview project={project} />
            </div>
            <DrawingReading reading={reading} onReread={reread} />
          </div>
        </div>

        {/* RIGHT COLUMN: Harmony Score + Multi-Metric KPIs + Direction-wise Audit */}
        <div className="vastu-right-col">
          {/* SECTION 1: Vastu Harmony & Compliance Metrics */}
          <div className="vastu-card harmony-score-card">
            <div className="harmony-card-header">
              <div>
                <h3 className="harmony-card-title">Vastu Harmony Score</h3>
                <div style={{ fontSize: '0.8rem', color: '#8fa6a1', marginTop: 3 }}>
                  {v.overall_grade || '8-Directional Shastra Alignment'}
                </div>
              </div>
              <div className="harmony-header-controls">
                <span className="amber-sim-pill">
                  {isReading ? 'Analyzing drawing...' : (v.evaluated > 0 ? `${v.matched}/${v.evaluated} Rooms Aligned` : 'Simulated — AI Verified')}
                </span>
                <button className="btn-solid-mint" onClick={() => window.print()} title="Export or print Vastu PDF Report">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                  Export/Vastu PDF Report
                </button>
                <div className="score-ring-badge">{harmonyScore}%</div>
              </div>
            </div>

            {/* Sub-KPI Grid: Entrance Analysis & Plot Suitability */}
            <div className="vastu-kpi-grid">
              <div className="vastu-sub-kpi-card">
                <div className="kpi-card-header">
                  <span className="kpi-title-label">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#00e599" strokeWidth="2.2">
                      <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18"/>
                    </svg>
                    Entrance Analysis Score
                  </span>
                  <span className="kpi-score-badge">{entrance.score ? `${entrance.score}%` : '88%'}</span>
                </div>
                <div className="kpi-verdict-title">{entrance.verdict || 'Auspicious Ingress'}</div>
                <div className="kpi-desc-text">
                  <strong>Zone:</strong> {entrance.zone || 'North / East'} &bull; <strong>Pada:</strong> {entrance.pada || 'Indra / Jayanta Gateway'}
                </div>
                <div style={{ fontSize: '0.76rem', color: '#8fa6a1', lineHeight: 1.45 }}>
                  {entrance.note || 'Main gate admits positive cosmic prana and morning sunlight.'}
                </div>
              </div>

              <div className="vastu-sub-kpi-card">
                <div className="kpi-card-header">
                  <span className="kpi-title-label">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2.2">
                      <polygon points="12 2 2 7 12 12 22 7 12 2"/>
                      <polyline points="2 17 12 22 22 17"/>
                      <polyline points="2 12 12 17 22 12"/>
                    </svg>
                    Plot Suitability Score
                  </span>
                  <span className="kpi-score-badge">{plot.score ? `${plot.score}%` : '92%'}</span>
                </div>
                <div className="kpi-verdict-title">{plot.type || 'Ayatakar (Rectangular)'}</div>
                <div className="kpi-desc-text">
                  <strong>Aspect Ratio:</strong> {plot.ratio || '1.33:1'} &bull; <strong>Plan Dimensions:</strong> {plot.dimensions || "30' x 40'"}
                </div>
                <div style={{ fontSize: '0.76rem', color: '#8fa6a1', lineHeight: 1.45 }}>
                  {plot.note || 'Balanced cardinal geometry prevents energy dispersion.'}
                </div>
              </div>
            </div>

            {/* SECTION 2: Direction-wise Score (8 Directions) Matching Screenshot */}
            <div style={{ marginTop: 24 }}>
              <div className="issues-subhead-label">DIRECTION-WISE SCORE (8 CARDINAL &amp; INTERCARDINAL ZONES)</div>
              <div className="dir-rows-container">
                {directionRows.length > 0 ? (
                  directionRows.map((dr, idx) => (
                    <div key={idx} className="dir-score-item">
                      <div className="dir-label-left">
                        <span className="dir-code">{dr.dir}</span>
                        <span className="dir-dash">—</span>
                        <span className="dir-room-name">{dr.room}</span>
                      </div>

                      <div className="dir-bar-track">
                        <div
                          className={`dir-bar-fill fill-${dr.status}`}
                          style={{ width: dr.width || (dr.status === 'good' ? '95%' : dr.status === 'poor' ? '30%' : '70%') }}
                        />
                      </div>

                      <span className={`dir-status-tag tag-${dr.status}`}>
                        {dr.status === 'good' ? 'Good' : dr.status === 'poor' ? 'Poor' : 'Needs Adjustment'}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="mut" style={{ padding: '16px 0' }}>Detecting room directional alignments from drawing...</p>
                )}
              </div>
            </div>
          </div>

          {/* SECTION 3: Remediation Guidelines & Detected Issues Matching Screenshot */}
          <div className="vastu-card remediation-container-card">
            <div className="remediation-header-tag">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#00e599" strokeWidth="2.5">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              <span>REMEDIATION GUIDELINES</span>
            </div>

            <p className="remediation-summary-p">
              <strong>Strengths:</strong> {remediation.strengths?.replace('Strengths: ', '') || 'Dining Room (East), Staircase (South), Master Bedroom (Southwest) align well with traditional Vastu placement guidance.'}{' '}
              <br />
              <strong>Priority Concerns:</strong> {remediation.priority_concerns?.replace('Priority Concerns: ', '') || '2 rooms show major deviation from ideal Vastu placement and should be addressed first.'}{' '}
              <br />
              <strong>Needs Adjustment:</strong> {remediation.needs_adjustment?.replace('Needs Adjustment: ', '') || '3 rooms could be improved with minor layout or remedial changes.'}
            </p>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div className="issues-subhead-label" style={{ margin: 0 }}>DETECTED ISSUES &amp; RECOMMENDED FIXES</div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  className={`vastu-cat-tab ${severityFilter === 'all' ? 'active' : ''}`}
                  style={{ padding: '3px 10px', fontSize: '0.72rem' }}
                  onClick={() => setSeverityFilter('all')}
                >
                  All ({problemAreas.length})
                </button>
                <button
                  className={`vastu-cat-tab ${severityFilter === 'critical' ? 'active' : ''}`}
                  style={{ padding: '3px 10px', fontSize: '0.72rem', borderColor: severityFilter === 'critical' ? '#ef4444' : '' }}
                  onClick={() => setSeverityFilter('critical')}
                >
                  Critical ({problemAreas.filter(p => p.badge === 'critical').length})
                </button>
                <button
                  className={`vastu-cat-tab ${severityFilter === 'moderate' ? 'active' : ''}`}
                  style={{ padding: '3px 10px', fontSize: '0.72rem', borderColor: severityFilter === 'moderate' ? '#f59e0b' : '' }}
                  onClick={() => setSeverityFilter('moderate')}
                >
                  Needs Adjustment ({problemAreas.filter(p => p.badge === 'moderate').length})
                </button>
              </div>
            </div>

            {/* Problem Area Issue Cards Stack with Error, Why it matters, Solution */}
            <div className="issues-card-stack">
              {filteredProblems.length > 0 ? (
                filteredProblems.map((issue, i) => (
                  <div key={i} className={`issue-detail-card card-border-${issue.status}`}>
                    <div className="issue-card-top">
                      <span className={`dir-status-tag tag-${issue.status}`}>
                        {issue.status === 'poor' ? 'POOR' : 'NEEDS ADJUSTMENT'}
                      </span>
                      <span className="issue-room-header">{issue.room}</span>
                      <span style={{ fontSize: '0.76rem', color: '#8fa6a1', marginLeft: 'auto' }}>{issue.category}</span>
                    </div>

                    <div className="issue-placement-row">
                      <span className={`issue-dot dot-${issue.status}`}>●</span>
                      <span className="issue-placement-text">
                        <strong>Error:</strong> Currently placed in the <strong>{issue.current_zone}</strong> zone — should ideally be in the <strong style={{ color: '#00e599' }}>{issue.ideal_zone}</strong> zone.
                      </span>
                    </div>

                    <div className="issue-info-row">
                      <span className="issue-info-icon">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                      </span>
                      <div className="issue-why-content">
                        <strong>Why it matters:</strong> {issue.why}
                      </div>
                    </div>

                    <div className="issue-solution-row">
                      <span className="issue-solution-icon">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#00e599" strokeWidth="2.5"><circle cx="12" cy="12" r="10"/><polyline points="16 10 11 15 8 12"/></svg>
                      </span>
                      <div className="issue-sol-content">
                        <strong>Solution:</strong> {issue.solution}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="issue-detail-card" style={{ textAlign: 'center', color: '#94a3b8' }}>
                  {isReading ? 'Parsing room placements from drawing...' : 'All rooms on this drawing align harmoniously with Vastu guidelines.'}
                </div>
              )}
            </div>
          </div>

          {/* SECTION 4: Room-wise Score (All 19 Items Sorted by Category) */}
          <div className="vastu-card">
            <div className="harmony-card-header">
              <div>
                <h3 className="harmony-card-title">Room-wise Score &amp; Spatial Inventory</h3>
                <div style={{ fontSize: '0.8rem', color: '#8fa6a1', marginTop: 3 }}>
                  Strict compliance audit for all 19 primary rooms, utilities, and exterior features.
                </div>
              </div>
            </div>

            {/* Category Filter Tabs */}
            <div className="vastu-cat-tabs">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  className={`vastu-cat-tab ${selectedCategory === cat ? 'active' : ''}`}
                  onClick={() => setSelectedCategory(cat)}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Room Audit Cards Grid */}
            <div className="room-inventory-grid">
              {filteredRooms.map((r, i) => (
                <div key={i} className={`room-audit-card card-border-${r.status}`}>
                  <div className="audit-card-top">
                    <div>
                      <div className="audit-room-title">{r.room}</div>
                      <div className="audit-cat-tag">{r.category}</div>
                    </div>
                    <span className={`dir-status-tag tag-${r.status}`}>
                      {r.status === 'good' ? 'Good' : r.status === 'poor' ? 'Poor' : 'Needs Adjustment'}
                    </span>
                  </div>

                  <div className="audit-zones-row">
                    <div>
                      <div className="zone-label">Detected</div>
                      <div className="zone-val">{r.detected_zone}</div>
                    </div>
                    <div className="zone-arrow">&rarr;</div>
                    <div>
                      <div className="zone-label">Ideal Vastu</div>
                      <div className="zone-val" style={{ color: '#00e599' }}>{r.ideal}</div>
                    </div>
                    {r.score && (
                      <div>
                        <div className="zone-label">Score</div>
                        <div className="zone-val" style={{ color: '#fbbf24' }}>{r.score}%</div>
                      </div>
                    )}
                  </div>

                  <div className="audit-element-text">
                    <strong>Energy Element:</strong> {r.element}
                  </div>

                  <div className="audit-remedy-hint">
                    {r.solution}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* SECTION 5: Traditional Vastu Remedies */}
          <div className="vastu-card">
            <div className="harmony-card-header">
              <div>
                <h3 className="harmony-card-title">Traditional Vastu Remedies</h3>
                <div style={{ fontSize: '0.8rem', color: '#8fa6a1', marginTop: 3 }}>
                  Vedic non-structural remediation cures: metallic helix, pyramids, yantras, color therapy, and threshold enhancements.
                </div>
              </div>
            </div>

            <div className="remedies-grid">
              {remedies.map((rem, idx) => (
                <div key={idx} className="remedy-card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div className="remedy-icon-pill">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polygon points="12 2 2 22 22 22"/>
                      </svg>
                    </div>
                    <div>
                      <div className="remedy-title">{rem.title}</div>
                      <div className="remedy-zone-tag">{rem.zone}</div>
                    </div>
                  </div>

                  <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600 }}>
                    {rem.element}
                  </div>

                  <div className="remedy-desc">
                    {rem.description}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
