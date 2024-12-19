import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ManageGradesPage.css';

function ManageGradesPage() {
  const [grades, setGrades] = useState([]);
  const [filteredGrades, setFilteredGrades] = useState([]);
  const [editingGradeId, setEditingGradeId] = useState(null);
  const [editedGrade, setEditedGrade] = useState({ ocenka: '' });
  const [error, setError] = useState('');
  const [studentFilter, setStudentFilter] = useState('');
  const [subjectFilter, setSubjectFilter] = useState('');

  // Состояния для новой оценки
  const [newGradeData, setNewGradeData] = useState({
    id_student: '',
    id_teacher: localStorage.getItem('id_teacher') || '',
    ocenka: '',
    date: '' // Формат: YYYY-MM-DD
  });

  const fetchGrades = async () => {
    try {
      const teacherId = localStorage.getItem('id_teacher'); 
      console.log("teacherId:", teacherId); // Для отладки

      const response = await axios.get('http://localhost:5000/api/grades', {
        params: { teacher_id: teacherId }
      });

      setGrades(response.data);
      setFilteredGrades(response.data);
    } catch (err) {
      console.error("Ошибка при получении оценок:", err);
      setError('Не удалось загрузить оценки.');
    }
  };

  useEffect(() => {
    fetchGrades();
  }, []);

  useEffect(() => {
    const filtered = grades.filter((grade) => {
      const studentMatch = grade.student_fio.toLowerCase().includes(studentFilter.toLowerCase());
      const subjectMatch = grade.nazvanie_predmeta.toLowerCase().includes(subjectFilter.toLowerCase());
      return studentMatch && subjectMatch;
    });
    setFilteredGrades(filtered);
  }, [studentFilter, subjectFilter, grades]);

  const handleEditClick = (grade) => {
    setEditingGradeId(grade.id_ocenki);
    setEditedGrade({ ocenka: grade.ocenka });
  };

  const handleCancelEdit = () => {
    setEditingGradeId(null);
    setEditedGrade({ ocenka: '' });
  };

  const handleSaveEdit = async (id_ocenki) => {
    try {
      const response = await axios.put(`http://localhost:5000/api/grades/${id_ocenki}`, editedGrade);
      console.log('Edit response:', response.data);  
      setGrades(grades.map((grade) => (grade.id_ocenki === id_ocenki ? response.data : grade)));
      setEditingGradeId(null);
      setEditedGrade({ ocenka: '' });
    } catch (err) {
      console.error("Ошибка при редактировании оценки:", err);
      setError('Не удалось обновить оценку.');
    }
  };

  const handleDelete = async (id_ocenki) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту оценку?')) return;
    try {
      await axios.delete(`http://localhost:5000/api/grades/${id_ocenki}`);
      setGrades(grades.filter((grade) => grade.id_ocenki !== id_ocenki));
    } catch (err) {
      console.error("Ошибка при удалении оценки:", err);
      setError('Не удалось удалить оценку.');
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEditedGrade((prevState) => ({ ...prevState, [name]: value }));
  };

  // Обработчики для новой оценки
  const handleNewGradeChange = (e) => {
    const { name, value } = e.target;
    setNewGradeData((prevState) => ({ ...prevState, [name]: value }));
  };

  const handleAddGrade = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://localhost:5000/api/grades/new', newGradeData);
      console.log('New grade added:', response.data);
      // После успешного добавления обновляем список оценок
      fetchGrades();
      // Сбрасываем поля формы
      setNewGradeData({
        id_student: '',
        id_teacher: localStorage.getItem('id_teacher') || '',
        ocenka: '',
        date: ''
      });
    } catch (err) {
      console.error("Ошибка при добавлении оценки:", err);
      setError('Не удалось добавить оценку.');
    }
  };

  return (
    <div className="manage-grades-page">
      <h2>Управление Оценками</h2>
      {error && <p className="error">{error}</p>}

      <div className="filters">
        <input
          type="text"
          placeholder="Фильтр по имени студента"
          value={studentFilter}
          onChange={(e) => setStudentFilter(e.target.value)}
        />
        <input
          type="text"
          placeholder="Фильтр по предмету"
          value={subjectFilter}
          onChange={(e) => setSubjectFilter(e.target.value)}
        />
      </div>

      <form onSubmit={handleAddGrade} className="add-grade-form">
        <h3>Добавить новую оценку</h3>
        <input
          type="text"
          name="id_student"
          placeholder="ID студента"
          value={newGradeData.id_student}
          onChange={handleNewGradeChange}
        />
        <input
          type="number"
          name="ocenka"
          placeholder="Оценка"
          value={newGradeData.ocenka}
          onChange={handleNewGradeChange}
          min="0"
          max="100"
        />
        <input
          type="date"
          name="date"
          value={newGradeData.date}
          onChange={handleNewGradeChange}
        />
        <button type="submit">Добавить оценку</button>
      </form>

      <table className="grades-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Оценка</th>
            <th>Студент</th>
            <th>Предмет</th>
            <th>Дата</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {filteredGrades.map((grade) => (
            <tr key={grade.id_ocenki}>
              <td>{grade.id_ocenki}</td>
              <td>
                {editingGradeId === grade.id_ocenki ? (
                  <input
                    type="number"
                    name="ocenka"
                    value={editedGrade.ocenka}
                    onChange={handleInputChange}
                    min="0"
                    max="100"
                  />
                ) : (
                  grade.ocenka
                )}
              </td>
              <td>{grade.student_fio}</td>
              <td>{grade.nazvanie_predmeta}</td>
              <td>{new Date(grade.date).toLocaleDateString()}</td>
              <td>
                {editingGradeId === grade.id_ocenki ? (
                  <>
                    <button onClick={() => handleSaveEdit(grade.id_ocenki)}>Сохранить</button>
                    <button onClick={handleCancelEdit}>Отмена</button>
                  </>
                ) : (
                  <>
                    <button onClick={() => handleEditClick(grade)}>Редактировать</button>
                    <button onClick={() => handleDelete(grade.id_ocenki)}>Удалить</button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ManageGradesPage;
