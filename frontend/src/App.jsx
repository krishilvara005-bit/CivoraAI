import { Link, Route, Routes } from 'react-router-dom';
import Shell from './components/Shell.jsx';
import ProjectLayout from './pages/ProjectLayout.jsx';
import Intro from './pages/Intro.jsx';
import Dashboard from './pages/Dashboard.jsx';
import ProjectHome from './pages/ProjectHome.jsx';
import Structure from './pages/Structure.jsx';
import Cost from './pages/Cost.jsx';
import Vastu from './pages/Vastu.jsx';

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Intro />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="projects/:id" element={<ProjectLayout />}>
          <Route index element={<ProjectHome />} />
          <Route path="structure" element={<Structure />} />
          <Route path="cost" element={<Cost />} />
          <Route path="vastu" element={<Vastu />} />
        </Route>
        <Route
          path="*"
          element={
            <div className="wrap">
              <h2>Page not found</h2>
              <p className="mut" style={{ margin: '10px 0 18px' }}>That page does not exist.</p>
              <Link className="btn" to="/dashboard">Go to the Dashboard</Link>
            </div>
          }
        />
      </Route>
    </Routes>
  );
}
