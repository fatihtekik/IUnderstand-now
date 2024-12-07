// src/App.js

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import LoginPage from './pages/LoginPage';
import GradesPage from './pages/GradesPage';
import DashboardPage from './pages/DashboardPage';
import ProfilePage from './pages/ProfilePage';
import ManageGradesPage from './pages/ManageGradesPage';
import './App.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(
    () => localStorage.getItem('isLoggedIn') === 'true'
  );
  const [userRole, setUserRole] = useState(
    () => localStorage.getItem('userRole') || 'student' // По умолчанию 'student'
  );

  const handleLogout = () => {
    console.log('handleLogout called');
    setIsLoggedIn(false);
    setUserRole('student'); // Сбрасываем роль на 'student'
    localStorage.setItem('isLoggedIn', 'false');
    localStorage.removeItem('id_student');
    localStorage.removeItem('userRole'); // Удаляем роль из localStorage
    console.log('User logged out');
  };

  useEffect(() => {
    console.log('App.js: isLoggedIn =', isLoggedIn, 'userRole =', userRole);
  }, [isLoggedIn, userRole]);

  return (
    <Router>
      <div className="app-layout">
        {isLoggedIn && <Sidebar onLogout={handleLogout} userRole={userRole} />} {/* Передаём userRole */}
        <div className={isLoggedIn ? 'content-with-sidebar' : 'content'}>
          <Routes>
            <Route path="/login" element={<LoginPage setIsLoggedIn={setIsLoggedIn} setUserRole={setUserRole} />} />
            <Route path="/" element={isLoggedIn ? <DashboardPage /> : <Navigate to="/login" />} />
            <Route path="/grades" element={isLoggedIn ? <GradesPage /> : <Navigate to="/login" />} />
            <Route
              path="/manage-grades"
              element={
                isLoggedIn && userRole === 'teacher' ? (
                  <ManageGradesPage />
                ) : (
                  <Navigate to="/" />
                )
              }
            />
            <Route path="/profile" element={isLoggedIn ? <ProfilePage /> : <Navigate to="/login" />} />
            <Route path="*" element={<Navigate to={isLoggedIn ? '/' : '/login'} />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
