import { useEffect } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';

export default function Shell() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return (
    <>
      <header className="top">
        <Link className="brand" to="/">
          <span className="bm"><img src="/logo-mark.webp" alt="" /></span>
          CIVORA AI
        </Link>
        <nav aria-label="Main">
          {pathname === '/' ? (
            <Link className="btn sm" to="/dashboard" style={{ color: '#1a0a00' }}>Enter Analyzer</Link>
          ) : (
            <NavLink to="/dashboard">Dashboard</NavLink>
          )}
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </>
  );
}
