import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import './ProfilePage.css';
import gifImage from "./anime-matching-pfp-matching-pfp.gif";

const ProfilePage = () => {
  const [studentInfo, setStudentInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(false); // Состояние загрузки
  const [error, setError] = useState(null); // Состояние ошибки
  const currentStudentId = localStorage.getItem('id_student'); // Получаем ID студента

  useEffect(() => {
    if (!currentStudentId) {
      setError('ID студента не найден. Пожалуйста, войдите в систему.');
      return;
    }

    setIsLoading(true);
    setError(null); 
    fetch(`http://localhost:5000/api/studentWithGroup?id_student=${currentStudentId}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error('Сетевая ошибка при загрузке данных.');
        }
        return response.json();
      })
      .then((data) => {
        setStudentInfo(data);
        setIsLoading(false); // Завершение загрузки
      })
      .catch((error) => {
        console.error('Ошибка загрузки данных:', error);
        setError('Не удалось загрузить данные профиля. Попробуйте позже.');
        setIsLoading(false); // Завершение загрузки при ошибке
      });
  }, [currentStudentId]);


  return (
    <div className="profile-page">
      <Sidebar />
      <div className="profile-container">
        {isLoading && (
          <div className="loader"></div>
        )}
        {error && <p className="error-message">{error}</p>}
        {!isLoading && !error && studentInfo && (
          <>
            <div className="profile-header">
              <img src={gifImage} alt="Profile Avatar" className="profile-avatar" />
              <div className="profile-info">
                <h2>{studentInfo.fio}</h2>
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
          </>
        )}
      </div>
    </div>
  );
};

export default ProfilePage;
