import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar'; // Боковая панель
import './ProfilePage.css'; // Стили для профиля

const ProfilePage = () => {
  const [studentInfo, setStudentInfo] = useState(null); // Информация о студенте
  const currentStudentId = localStorage.getItem('id_student'); // Получаем ID студента из LocalStorage

  useEffect(() => {
    // Загружаем данные студента с сервера
    fetch(`http://localhost:5000/api/studentWithGroup?id_student=${currentStudentId}`)
      .then((response) => response.json())
      .then((data) => {
        setStudentInfo(data);
      })
      .catch((error) => {
        console.error('Ошибка загрузки информации о студенте:', error);
      });
  }, [currentStudentId]);

  return (
    <div className="profile-page">
      <Sidebar />
      <div className="profile-content">
        <h1>Профиль студента</h1>
        {studentInfo ? (
          <div className="profile-details">
            <p><strong>ФИО:</strong> {studentInfo.fio}</p>
            <p><strong>Группа:</strong> {studentInfo.group}</p>
          </div>
        ) : (
          <p>Загрузка информации о студенте...</p>
        )}
      </div>
    </div>
  );
};

export default ProfilePage;
