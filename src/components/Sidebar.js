import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Sidebar.css'; // Подключаем стили

const Sidebar = ({ setIsLoggedIn }) => {
  const navigate = useNavigate(); // Хук для навигации

  const handleLogout = () => {
    localStorage.setItem('isLoggedIn', false); // Сбрасываем статус авторизации
    localStorage.removeItem('id_student'); // Удаляем ID студента, если нужно
    // setIsLoggedIn(false); // Обновляем состояние авторизации
    navigate('/login'); // Перенаправляем на страницу логина
  };

  return (
    <div className="sidebar">
      <div className="profile">
        <img src="/path-to-avatar.jpg" alt="Avatar" className="avatar" />
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
