import axios from "axios";

const API_URL = `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/saved-quizzes`;
const DUMMY_USER_ID = "dummy-user-123"; // until auth is ready

// Save a quiz
export const saveQuiz = async (title: string, quizData: any) => {
  const res = await axios.post(`${API_URL}/save`, {
    user_id: DUMMY_USER_ID,
    title,
    quiz_data: quizData,
  });
  return res.data;
};

// Get all saved quizzes for a user
export const getSavedQuizzes = async () => {
  const res = await axios.get(`${API_URL}/${DUMMY_USER_ID}`);
  return res.data;
};

// Delete a saved quiz
export const deleteSavedQuiz = async (quizId: string) => {
  const res = await axios.delete(`${API_URL}/${DUMMY_USER_ID}/${quizId}`);
  return res.data;
};
