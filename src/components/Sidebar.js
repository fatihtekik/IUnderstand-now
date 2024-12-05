import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Sidebar.css'; // Подключаем стили
import asLogo from './asLogo.jpg';



const Sidebar = ({ setIsLoggedIn }) => {
  const navigate = useNavigate(); 

  const handleLogout = () => {
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
          <li><Link to="/profile">Профиль</Link></li>
          <li><button onClick={handleLogout}>Выйти</button></li>
        </ul>
      </nav>
    </div>
  );
};

export default Sidebar;
