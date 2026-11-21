import { Link } from 'react-router-dom';

const STEPS = [
  ['Create a project', 'Name it on the Dashboard so you can find it again.'],
  ['Upload your plan', 'Choose a JPG, PNG, PDF, DXF or DWG file from your computer.'],
  ['Run an analyzer', 'Open the Structure, Cost or Vastu analyzer for that plan.'],
];
const ANALYZERS = [
  ['Structure Plan Analyzer', 'Enter floors, area, seismic zone, soil and concrete grade. Anything you leave out stays marked as not provided.'],
  ['Cost Estimation Analyzer', 'Combine floors and area with a rate you enter to get a total and a likely range. No rate is assumed.'],
  ['Vastu Plan Analyzer', 'Confirm north, place each room in one of eight zones, and compare it with a traditional rule set.'],
];

export default function Intro() {
  return (
    <>
      <section className="hero">
        <div className="in">
          <div>
            <h1>Review your house plan before you build</h1>
            <p>CIVORA AI checks a residential drawing for structure, cost and Vastu. Create a project, upload your plan from your computer, and see what the plan shows and what it leaves out.</p>
            <Link className="btn" to="/dashboard">Enter Analyzer</Link>
            <small>Preliminary decision support. Not certified engineering.</small>
          </div>
          <img className="logo" src="/logo.webp" alt="CIVORA AI logo with a skyline, crane and house forming the letters C and A" />
        </div>
      </section>
      <section className="sec">
        <h2>From drawing to review in three steps</h2>
        <div className="c3">
          {STEPS.map(([t, d], i) => (
            <div className="card" key={t}><span className="k">Step {i + 1}</span><h3>{t}</h3><p className="mut">{d}</p></div>
          ))}
        </div>
      </section>
      <section className="sec">
        <h2>Three analyzers</h2>
        <div className="c3">
          {ANALYZERS.map(([t, d]) => <div className="card" key={t}><h3>{t}</h3><p className="mut">{d}</p></div>)}
        </div>
      </section>
      <footer className="foot">
        CIVORA AI gives decision support only. Its results are not certified drawings, approvals or quotations, and a licensed engineer or architect should review any real project. Vastu is a traditional belief system.
      </footer>
    </>
  );
}
