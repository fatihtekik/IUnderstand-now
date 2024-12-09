// src/pages/GradesPage.js

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './GradesPage.css';

// Функция для конвертации оценки в GPA
function getGPAFromScore(score) {
  if (95 <= score && score <= 100) return 4.0;
  else if (90 <= score && score < 95) return 3.67;
  else if (85 <= score && score < 90) return 3.33;
  else if (80 <= score && score < 85) return 3.0;
  else if (75 <= score && score < 80) return 2.67;
  else if (70 <= score && score < 75) return 2.33;
  else if (65 <= score && score < 70) return 2.0;
  else if (60 <= score && score < 65) return 1.67;
  else if (55 <= score && score < 60) return 1.33;
  else if (50 <= score && score < 55) return 1.0;
  else return 0.0;
}

function GradesPage() {
  const [allData, setAllData] = useState([]);
  const [data, setData] = useState([]);
  const [viewMode, setViewMode] = useState('all');
  const [subjectFilter, setSubjectFilter] = useState('');
  const [subjectAverages, setSubjectAverages] = useState([]); // Средние значения по предметам
  const [isLoading, setIsLoading] = useState(false); // Состояние загрузки
  const [error, setError] = useState(null); // Состояние ошибки
  const navigate = useNavigate();

  const currentStudentId = Number(localStorage.getItem('id_student'));

  // Загрузка данных для режима 'subject'
  useEffect(() => {
    if (viewMode === 'subject' && currentStudentId) {
      setIsLoading(true); // Начало загрузки
      setError(null); // Сброс ошибки
      fetch(`http://localhost:5000/api/dataById?id_student=${currentStudentId}`)
        .then((response) => {
          if (!response.ok) {
            throw new Error('Сетевая ошибка');
          }
          return response.json();
        })
        .then((fetchedData) => {
          const dataWithGPA = fetchedData.map((item) => ({
            ...item,
            gpa: getGPAFromScore(item.ocenka),
          }));
          setData(dataWithGPA);
          setIsLoading(false); // Завершение загрузки
        })
        .catch((error) => {
          console.error('Ошибка при загрузке данных:', error);
          setError('Не удалось загрузить оценки. Попробуйте позже.');
          setIsLoading(false); // Завершение загрузки при ошибке
        });
    }
  }, [viewMode, currentStudentId]);

  // Загрузка данных для режима 'all'
  useEffect(() => {
    if (!currentStudentId) {
      navigate('/login'); // Если ID студента отсутствует
    } else if (viewMode === 'all') {
      setIsLoading(true); // Начало загрузки
      setError(null); // Сброс ошибки
      fetch('http://localhost:5000/api/data')
        .then((response) => {
          if (!response.ok) {
            throw new Error('Сетевая ошибка');
          }
          return response.json();
        })
        .then((fetchedData) => {
          const dataWithGPA = fetchedData.map((item) => ({
            ...item,
            gpa: getGPAFromScore(item.ocenka),
          }));
          setAllData(dataWithGPA);
          setData(dataWithGPA);
          setIsLoading(false); // Завершение загрузки
        })
        .catch((error) => {
          console.error('Ошибка при загрузке данных:', error);
          setError('Не удалось загрузить оценки. Попробуйте позже.');
          setIsLoading(false); // Завершение загрузки при ошибке
        });
    }
  }, [currentStudentId, navigate, viewMode]);

  // Рассчёт средних значений по предметам
  useEffect(() => {
    if (viewMode === 'gpa') {
      const groupedData = data.reduce((acc, item) => {
        if (!acc[item.nazvanie_predmeta]) {
          acc[item.nazvanie_predmeta] = { totalScore: 0, count: 0 };
        }
        acc[item.nazvanie_predmeta].totalScore += item.ocenka;
        acc[item.nazvanie_predmeta].count += 1;
        return acc;
      }, {});

      const averages = Object.keys(groupedData).map((subject) => ({
        subject,
        averageScore: (groupedData[subject].totalScore / groupedData[subject].count).toFixed(2),
        gpa: getGPAFromScore(
          groupedData[subject].totalScore / groupedData[subject].count
        ).toFixed(2),
      }));

      setSubjectAverages(averages);
    }
  }, [viewMode, data]);

  const handleViewModeChange = (mode) => {
    setViewMode(mode);
    if (mode === 'all') {
      setData(allData);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('id_student');
    navigate('/login');
  };

  return (
    <div className="grades-page">
      <h1>Оценки студентов</h1>
      <div className="controls">
        <button onClick={() => handleViewModeChange('all')}>Все оценки</button>
        <button onClick={() => setViewMode('subject')}>Оценки по предмету</button>
        <button onClick={() => setViewMode('gpa')}>Посчитать GPA</button>
        <button onClick={handleLogout}>Выйти</button>
      </div>

      {/* Индикатор загрузки */}
      {isLoading && (
        <div className="loader"></div> // Используем спиннер
      )}

      {/* Сообщение об ошибке */}
      {error && <p className="error-message">{error}</p>}

      {/* Режим: Все оценки */}
      {!isLoading && !error && viewMode === 'all' && (
        <table className="grades-page-table">
          <thead>
            <tr>
              <th>Оценка</th>
              <th>Студент</th>
              <th>Предмет</th>
              <th>Дата</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr key={index}>
                <td>{row.ocenka}</td>
                <td>{row.fio}</td>
                <td>{row.nazvanie_predmeta}</td>
                <td>{row.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Режим: Оценки по предмету */}
      {!isLoading && !error && viewMode === 'subject' && (
        <div>
          <label htmlFor="subject">Выберите предмет:</label>
          <select
            id="subject"
            value={subjectFilter}
            onChange={(e) => setSubjectFilter(e.target.value)}
          >
            <option value="">Все предметы</option>
            {Array.from(new Set(data.map((row) => row.nazvanie_predmeta))).map(
              (subject, index) => (
                <option key={index} value={subject}>
                  {subject}
                </option>
              )
            )}
          </select>
          <table className="grades-page-table">
            <thead>
              <tr>
                <th>Оценка</th>
                <th>Студент</th>
                <th>Дата</th>
              </tr>
            </thead>
            <tbody>
              {data
                .filter((row) =>
                  subjectFilter ? row.nazvanie_predmeta === subjectFilter : true
                )
                .map((row, index) => (
                  <tr key={index}>
                    <td>{row.ocenka}</td>
                    <td>{row.fio}</td>
                    <td>{row.date}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Режим: GPA */}
      {!isLoading && !error && viewMode === 'gpa' && (
        <div>
          <h2>Средние оценки и GPA по предметам</h2>
          <table className="grades-page-table">
            <thead>
              <tr>
                <th>Предмет</th>
                <th>Средняя оценка</th>
                <th>Средний GPA</th>
              </tr>
            </thead>
            <tbody>
              {subjectAverages.map((subject, index) => (
                <tr key={index}>
                  <td>{subject.subject}</td>
                  <td>{subject.averageScore}</td>
                  <td>{subject.gpa}</td>
                </tr>
              ))}
              {/* Итоговая строка */}
              <tr style={{ fontWeight: 'bold', backgroundColor: '#f1f1f1' }}>
                <td>Итог</td>
                <td>
                  {subjectAverages.length > 0
                    ? (
                        subjectAverages.reduce(
                          (sum, subj) => sum + parseFloat(subj.averageScore),
                          0
                        ) / subjectAverages.length
                      ).toFixed(2)
                    : 'Нет данных'}
                </td>
                <td>
                  {subjectAverages.length > 0
                    ? (
                        subjectAverages.reduce(
                          (sum, subj) => sum + parseFloat(subj.gpa),
                          0
                        ) / subjectAverages.length
                      ).toFixed(2)
                    : 'Нет данных'}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default GradesPage;
