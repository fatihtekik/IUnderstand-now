// src/components/Sidebar.js

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Sidebar.css';
import asLogo from './asLogo.jpg';
import PropTypes from 'prop-types';

const Sidebar = ({ onLogout, userRole }) => {
  console.log('Sidebar props:', { onLogout, userRole }); // Отладка
  const navigate = useNavigate(); 

  const handleLogout = () => {
    console.log('handleLogout in Sidebar called'); // Отладка
    localStorage.setItem('isLoggedIn', false); 
    localStorage.removeItem('id_student'); 
    navigate('/login');
  };

  return (
    <div className="sidebar">
      <div className="profile">
        <img src={asLogo} alt="Avatar" className="avatar" />
        <h3>Имя пользователя</h3>
      </div>
      <nav>
        <ul>
          <li><Link to="/">Главная</Link></li>
          <li><Link to="/grades">Оценки</Link></li>
          {userRole === 'teacher' && (
            <li><Link to="/manage-grades">Управление Оценками</Link></li>
          )} 
          <li><Link to="/profile">Профиль</Link></li>
          <li><button onClick={handleLogout}>Выйти</button></li>
        </ul>
      </nav>
    </div>
  );
};

// Проверка типов пропсов
Sidebar.propTypes = {
  onLogout: PropTypes.func.isRequired,
  userRole: PropTypes.string.isRequired,
};

export default Sidebar;
