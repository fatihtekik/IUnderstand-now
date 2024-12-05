import React from 'react';
import Sidebar from '../components/Sidebar';
import './DashboardPage.css';

const DashboardPage = () => {
  return (
    <div className="dashboard">
      <Sidebar />
      <div className="content">
        <div className="main">
          <h1 className="welcome-title">Добро пожаловать в систему оценок</h1>
          <div className="cards-container">
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
            <div className="card">
              <h3>Современно</h3>
              <p>Используйте современный интерфейс для быстрого доступа к данным.</p>
            </div>
            <div className="card">
              <h3>Удобно</h3>
              <p>Всё, что вам нужно, находится под рукой — интуитивно и просто.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
