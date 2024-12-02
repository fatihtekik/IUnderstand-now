import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import LoginPage from './pages/LoginPage';
import GradesPage from './pages/GradesPage';
import DashboardPage from './pages/DashboardPage';
import ProfilePage from './pages/ProfilePage';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(
    () => localStorage.getItem('isLoggedIn') === 'true'
  );

  useEffect(() => {
    localStorage.setItem('isLoggedIn', isLoggedIn);
  }, [isLoggedIn]);

  return (
    <Router>
      <div className="app-layout">
        {isLoggedIn && <Sidebar setIsLoggedIn={setIsLoggedIn} />} {/* Сайдбар виден только если авторизован */}
        <div className={isLoggedIn ? 'content-with-sidebar' : 'content'}>
          <Routes>
            <Route path="/login" element={<LoginPage setIsLoggedIn={setIsLoggedIn} />} />
            <Route path="/" element={isLoggedIn ? <DashboardPage /> : <Navigate to="/login" />} />
            <Route path="/grades" element={isLoggedIn ? <GradesPage /> : <Navigate to="/login" />} />
            <Route path="/profile" element={isLoggedIn ? <ProfilePage /> : <Navigate to="/login" />} />
            <Route path="*" element={<Navigate to={isLoggedIn ? '/' : '/login'} />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
