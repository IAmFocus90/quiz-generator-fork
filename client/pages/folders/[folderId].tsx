"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/router";
import toast from "react-hot-toast";
import {
  getFolderById,
  removeQuizFromFolder,
} from "../../lib/functions/folders";
import MoveQuizModal from "../../components/home/folders/MoveQuizModal";

const FolderView = () => {
  const router = useRouter();
  const { folderId } = router.query;

  const [folder, setFolder] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [moveModalOpen, setMoveModalOpen] = useState(false);
  const [selectedQuiz, setSelectedQuiz] = useState<any>(null);

  useEffect(() => {
    if (!folderId) return;
    const fetchFolder = async () => {
      try {
        setLoading(true);
        const res = await getFolderById(folderId as string);
        setFolder(res);
      } catch (err) {
        console.error(err);
        toast.error("Failed to load folder");
      } finally {
        setLoading(false);
      }
    };
    fetchFolder();
  }, [folderId]);

  const handleDeleteQuiz = async (quizId: string) => {
    try {
      await removeQuizFromFolder(folderId as string, quizId);
      toast.success("Quiz deleted successfully");
      setFolder((prev: any) =>
        prev
          ? {
              ...prev,
              quizzes: prev.quizzes.filter((q: any) => q._id !== quizId),
            }
          : prev,
      );
    } catch (err) {
      console.error(err);
      toast.error("Error deleting quiz");
    }
  };

  const handleMoveQuiz = (quiz: any) => {
    setSelectedQuiz(quiz);
    setMoveModalOpen(true);
  };

  // Safe date formatting
  const formatDate = (date: string) => {
    if (!date) return "Date unavailable";
    const parsed = new Date(date);
    return isNaN(parsed.getTime())
      ? "Date unavailable"
      : parsed.toLocaleDateString();
  };

  const getQuizTitle = (quiz: any) =>
    quiz.title || quiz.quiz_data?.title || "Untitled Quiz";

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen text-gray-600">
        <p>Loading folder...</p>
      </div>
    );
  }

  if (!folder) {
    return (
      <div className="flex justify-center items-center h-screen text-gray-500">
        <p>Folder not found.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* NAVBAR */}
      <nav className="bg-navy-600 text-white px-6 py-4 flex justify-between items-center shadow-md">
        <h1 className="text-xl font-semibold">📁 {folder.name}</h1>
        <button
          onClick={() => router.back()}
          className="bg-white text-navy-600 px-4 py-2 rounded-lg hover:bg-gray-100 font-medium"
        >
          Back
        </button>
      </nav>

      {/* HEADER */}
      <header className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-navy-800 mb-1">
          Open Folder: {folder.name}
        </h2>
        <p className="text-sm text-gray-500">
          {folder.quizzes?.length || 0} quizzes • Created on{" "}
          {formatDate(folder.created_at)}
        </p>
      </header>

      {/* QUIZZES */}
      <main className="flex-1 p-6 grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {folder.quizzes.length === 0 ? (
          <div className="col-span-full text-center text-gray-500">
            <p>No quizzes in this folder.</p>
          </div>
        ) : (
          folder.quizzes.map((quiz: any) => (
            <div
              key={quiz._id}
              className="border rounded-2xl p-4 shadow-sm bg-white hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                <h3 className="text-navy-800 font-semibold mb-1 truncate">
                  {getQuizTitle(quiz)}
                </h3>
                <p className="text-sm text-gray-500 mb-2">
                  Added on {formatDate(quiz.created_at || quiz.added_at)}
                </p>

                {/* Quiz content preview */}
                {quiz.quiz_data && (
                  <div className="text-sm text-gray-600 mt-2 bg-gray-50 p-2 rounded-md border">
                    <p>
                      <strong>Category:</strong>{" "}
                      {quiz.quiz_data.category || "N/A"}
                    </p>
                    <p>
                      <strong>Type:</strong>{" "}
                      {quiz.quiz_data.question_type || "N/A"}
                    </p>

                    {quiz.quiz_data.questions?.length > 0 && (
                      <div className="mt-2">
                        <p className="font-medium text-gray-700 mb-1">
                          Preview Question:
                        </p>
                        <p className="italic text-gray-500 line-clamp-2">
                          {quiz.quiz_data.questions[0].question}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Buttons */}
              <div className="flex justify-between items-center mt-4">
                <button
                  onClick={() =>
                    router.push(`/saved_quizzes/${quiz.original_quiz_id}`)
                  }
                  className="text-sm px-3 py-1 bg-navy-600 text-white rounded-lg hover:bg-navy-700"
                >
                  View
                </button>
                <button
                  onClick={() => handleMoveQuiz(quiz)}
                  className="text-sm px-3 py-1 bg-blue-100 text-navy-700 rounded-lg hover:bg-blue-200"
                >
                  Move
                </button>
                <button
                  onClick={() => handleDeleteQuiz(quiz._id)}
                  className="text-sm px-3 py-1 bg-red-100 text-red-600 rounded-lg hover:bg-red-200"
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </main>

      {/* FOOTER */}
      <footer className="bg-navy-600 text-white py-4 text-center mt-auto">
        <p className="text-sm">&copy; {new Date().getFullYear()} HQuiz</p>
      </footer>

      <MoveQuizModal
        isOpen={moveModalOpen}
        onClose={() => setMoveModalOpen(false)}
        quiz={selectedQuiz}
      />
    </div>
  );
};

export default FolderView;
