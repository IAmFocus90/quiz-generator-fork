"use client";

import React, { useEffect, useState } from "react";
import toast from "react-hot-toast";
import {
  getSavedQuizzes,
  deleteSavedQuiz,
} from "../../lib/functions/savedQuiz";

interface SavedQuiz {
  _id: string;
  title: string;
  created_at: string;
  quiz_data: any;
}

const SavedQuizzesPage = () => {
  const [quizzes, setQuizzes] = useState<SavedQuiz[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null); // modal control
  const userId = "dummy-user-123";

  // Fetch saved quizzes
  useEffect(() => {
    const fetchQuizzes = async () => {
      try {
        const data = await getSavedQuizzes();
        setQuizzes(data || []);
      } catch (err) {
        console.error("Error fetching saved quizzes:", err);
        toast.error("❌ Failed to load saved quizzes.");
      } finally {
        setLoading(false);
      }
    };
    fetchQuizzes();
  }, []);

  // Handle delete
  const handleDelete = async (quizId: string) => {
    try {
      setDeleting(quizId);
      await deleteSavedQuiz(quizId);
      setQuizzes((prev) => prev.filter((quiz) => quiz._id !== quizId));
      toast.success("✅ Quiz deleted successfully!");
    } catch (err) {
      console.error("Error deleting quiz:", err);
      toast.error("❌ Failed to delete quiz.");
    } finally {
      setDeleting(null);
      setConfirmDelete(null); // close modal
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#0a3264]"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Your Saved Quizzes</h1>
      {quizzes.length === 0 ? (
        <p>No saved quizzes yet.</p>
      ) : (
        <ul className="space-y-4">
          {quizzes.map((quiz) => (
            <li
              key={quiz._id}
              className="p-4 border rounded-lg shadow-md flex justify-between items-center"
            >
              <div>
                <h2 className="text-lg font-semibold">{quiz.title}</h2>
                <p className="text-sm text-gray-500">
                  Saved on {new Date(quiz.created_at).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => setConfirmDelete(quiz._id)} // ✅ trigger modal
                disabled={deleting === quiz._id}
                className="text-red-600 hover:underline disabled:opacity-50"
              >
                {deleting === quiz._id ? "Deleting..." : "Delete"}
              </button>
            </li>
          ))}
        </ul>
      )}

      {/* Confirmation Modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-xl shadow-lg max-w-sm w-full">
            <h2 className="text-lg font-bold mb-3 text-[#0a3264]">
              Confirm Delete
            </h2>
            <p className="text-sm text-gray-600 mb-6">
              Are you sure you want to delete this quiz? This action cannot be
              undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmDelete(null)}
                className="px-4 py-2 rounded-lg border text-gray-600 hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(confirmDelete)}
                className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
                disabled={deleting === confirmDelete}
              >
                {deleting === confirmDelete ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SavedQuizzesPage;
