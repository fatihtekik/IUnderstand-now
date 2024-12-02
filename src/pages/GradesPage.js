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
  const [gpa, setGpa] = useState(null); // Средний GPA

  const navigate = useNavigate();
  const currentStudentId = Number(localStorage.getItem('id_student'));

  // Загрузка всех данных
  useEffect(() => {
    if (!currentStudentId) {
      navigate('/login'); // Если ID студента отсутствует
    } else if (viewMode === 'all') {
      fetch('http://localhost:5000/api/data')
        .then((response) => response.json())
        .then((fetchedData) => {
          // Преобразуем каждую оценку в её GPA-эквивалент
          const dataWithGPA = fetchedData.map((item) => ({
            ...item,
            gpa: getGPAFromScore(item.ocenka),
          }));
          setAllData(dataWithGPA);
          setData(dataWithGPA);
        })
        .catch((error) => console.error('Ошибка при загрузке данных:', error));
    }
  }, [currentStudentId, navigate, viewMode]);

  // Загрузка данных "Мои оценки" и расчёт GPA
  useEffect(() => {
    if (viewMode === 'subject' && currentStudentId) {
      fetch(`http://localhost:5000/api/dataById?id_student=${currentStudentId}`)
        .then((response) => response.json())
        .then((filteredData) => {
          // Преобразуем оценки в GPA
          const dataWithGPA = filteredData.map((item) => ({
            ...item,
            gpa: getGPAFromScore(item.ocenka),
          }));
          setData(dataWithGPA);

          // Рассчитываем средний GPA
          const totalGPA = dataWithGPA.reduce((sum, item) => sum + item.gpa, 0);
          const calculatedGpa =
            dataWithGPA.length > 0 ? (totalGPA / dataWithGPA.length).toFixed(2) : 0;

          setGpa(calculatedGpa);
        })
        .catch((error) => console.error('Ошибка при загрузке данных для студента:', error));
    }
  }, [viewMode, currentStudentId]);

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

      {/* Режим: Все оценки */}
      {viewMode === 'all' && (
        <table className="grades-page-table">
          <thead>
            <tr>
              <th>Айди оценки</th>
              <th>Оценка</th>
              <th>GPA</th>
              <th>Студент</th>
              <th>Предмет</th>
              <th>Дата</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr key={index}>
                <td>{row.id_ocenki}</td>
                <td>{row.ocenka}</td>
                <td>{row.gpa}</td>
                <td>{row.fio}</td>
                <td>{row.nazvanie_predmeta}</td>
                <td>{row.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Режим: Оценки по предмету */}
      {viewMode === 'subject' && (
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
                <th>Айди оценки</th>
                <th>Оценка</th>
                <th>GPA</th>
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
                    <td>{row.id_ocenki}</td>
                    <td>{row.ocenka}</td>
                    <td>{row.gpa}</td>
                    <td>{row.fio}</td>
                    <td>{row.date}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Режим: GPA */}
      {viewMode === 'gpa' && (
        <div className="gpa">
          <h2>Ваш GPA: {gpa || 'Нет данных'}</h2>
        </div>
      )}
    </div>
  );
}

export default GradesPage;
