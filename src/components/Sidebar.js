

import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Sidebar.css'; // Ваши стили для сайдбара
import asLogo from './asLogo.jpg'; // Ваш логотип

const Sidebar = () => {
  const navigate = useNavigate();
  const [userRole, setUserRole] = useState('student'); // Значение по умолчанию

  useEffect(() => {
    // Извлечение роли пользователя из localStorage
    const role = localStorage.getItem('userRole');
    if (role) {
      setUserRole(role);
    }
  }, []);

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  return (
    <div className="sidebar">
      <div className="profile">
        <img src={asLogo} alt="Avatar" className="avatar" />
        <h3>Пользователь</h3>
        <p>{userRole === 'teacher' ? 'Преподаватель' : 'Ученик'}</p>
      </div>
      <nav>
        <ul>
          <li><Link to="/">Главная</Link></li>
          {userRole === 'student' && (
            <>
              <li><Link to="/grades">Оценки</Link></li>
              {/* Другие кнопки для студентов */}
            </>
          )}
          {userRole === 'teacher' && (
            <>
              <li><Link to="/manage-grades">Управление оценками</Link></li>
            </>
          )}
          <li><Link to="/profile">Профиль</Link></li>
          <li><button onClick={handleLogout}>Выйти</button></li>
        </ul>
      </nav>
    </div>
  );
};

export default Sidebar;
