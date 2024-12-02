import React from 'react';
import Sidebar from '../components/Sidebar';
import './DashboardPage.css'; // Подключаем стили для главной страницы

const DashboardPage = () => {
  return (
    <div className="dashboard">
      <Sidebar />
      <div className="content">
        <div className="main">
          <h1 className="welcome-title">Добро пожаловать в систему оценок</h1>
          <p className="description">
            Здесь вы можете отслеживать свои оценки, анализировать успеваемость и получать статистику.
          </p>
          <div className="cards-container">
            {/* Первые три карточки */}
            <div className="card">
              <h3>Все оценки</h3>
              <p>Просматривайте все оценки студентов и анализируйте их успеваемость.</p>
            </div>
            <div className="card">
              <h3>Рассчитать GPA</h3>
              <p>Получите статистику по среднему баллу (GPA) на основе ваших оценок.</p>
            </div>
            <div className="card">
              <h3>Оценки по предмету</h3>
              <p>Анализируйте успеваемость по конкретным предметам.</p>
            </div>

            {/* Добавленные карточки */}
            <div className="card">
              <h3>Современно</h3>
              <p>Используйте современный интерфейс для быстрого доступа к данным.</p>
            </div>
            <div className="card">
              <h3>Удобно</h3>
              <p>Всё, что вам нужно, находится под рукой — интуитивно и просто.</p>
            </div>
            <div className="card">
              <h3>Круто и прикольно</h3>
              <p>Эта система создана, чтобы сделать вашу учёбу более увлекательной!</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
