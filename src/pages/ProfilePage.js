import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import './ProfilePage.css';
import gifImage from "./anime-matching-pfp-matching-pfp.gif";


const ProfilePage = () => {
  const [studentInfo, setStudentInfo] = useState(null);
  const currentStudentId = localStorage.getItem('id_student'); // Получаем ID студента

  useEffect(() => {
    // Загружаем данные студента с сервера
    fetch(`http://localhost:5000/api/studentWithGroup?id_student=${currentStudentId}`)
      .then((response) => response.json())
      .then((data) => setStudentInfo(data))
      .catch((error) => console.error('Ошибка загрузки данных:', error));
  }, [currentStudentId]);

  if (!studentInfo) {
    return <p>Загрузка...</p>; // Отображаем, пока данные не загрузились
  }

  return (
    <div className="profile-page">
      <Sidebar />
      <div className="profile-container">
        <div className="profile-header">
          <img src={gifImage} alt="Profile Avatar" className="profile-avatar" />
          <div className="profile-info">
            <h2>{studentInfo.fio}</h2>
            <p className="location">Группа: {studentInfo.group}</p>
          </div>
        </div>
        <div className="profile-details">
          <div className="profile-section">
            <h3>Информация о студенте</h3>
            <p><strong>ФИО:</strong> {studentInfo.fio}</p>
            <p><strong>ИИН:</strong> {studentInfo.iin}</p>
            <p><strong>Группа:</strong> {studentInfo.group}</p>
          </div>
          <div className="profile-section">
            <h3>Контактная информация</h3>
            <p><strong>Телефон:</strong> +7 123 456 78 90</p>
            <p><strong>Email:</strong> student@example.com</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
