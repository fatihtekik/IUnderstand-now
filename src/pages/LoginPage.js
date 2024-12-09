// src/pages/LoginPage.js

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './login.css';

function LoginPage({ setIsLoggedIn, setUserRole }) { 
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch('http://localhost:5000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login, password }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Login successful:', data);
        localStorage.setItem('id_student', data.id_student);
        setIsLoggedIn(true);
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('userRole', data.role); // Сохраняем роль
        setUserRole(data.role); // Обновляем состояние роли
        navigate('/');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Ошибка авторизации');
        console.log('Login failed:', errorData);
      }
    } catch (err) {
      setError('Ошибка соединения с сервером');
      console.error('Connection error:', err);
    }
  };

  return (
    <div className='body'>
      <div className="login-container">
        <h2>Вход</h2>
        <form onSubmit={handleLogin}>
          <label>
            Логин:
            <input
              type="text"
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              required
            />
          </label>
          <label>
            Пароль:
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          <button type="submit">Войти</button>
        </form>
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  );
}

export default LoginPage;
