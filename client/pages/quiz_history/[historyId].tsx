"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import toast from "react-hot-toast";
import NavBar from "../../components/home/NavBar";
import Footer from "../../components/home/Footer";
import RequireAuth from "../../components/auth/RequireAuth";
import { getQuizHistoryItem } from "../../lib/functions/getUserQuizHistory";

interface QuizHistoryQuestion {
  question: string;
  options?: string[];
  answer: string;
}

interface QuizHistoryItem {
  id?: string;
  _id?: string;
  created_at?: string;
  quiz_name?: string;
  question_type: string;
  difficulty_level?: string;
  profession?: string;
  audience_type?: string;
  custom_instruction?: string;
  questions: QuizHistoryQuestion[];
}

export default function QuizHistoryDetailsPage() {
  const router = useRouter();
  const { historyId } = router.query;
  const [item, setItem] = useState<QuizHistoryItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!historyId || Array.isArray(historyId)) return;

    const fetchItem = async () => {
      try {
        const response = await getQuizHistoryItem(historyId);
        setItem(response);
      } catch (error) {
        console.error("Failed to fetch quiz history item:", error);
        toast.error("Failed to load quiz history details.");
      } finally {
        setLoading(false);
      }
    };

    fetchItem();
  }, [historyId]);

  return (
    <RequireAuth
      title="Quiz History Details"
      description="Sign in to view quiz history details."
    >
      <div className="flex flex-col min-h-screen bg-gray-100">
        <NavBar />
        <main className="flex-1 px-4 sm:px-6 md:px-8 py-8">
          <div className="max-w-4xl mx-auto">
            <button
              onClick={() => router.push("/quiz_history")}
              className="mb-4 text-sm text-blue-600 hover:underline"
            >
              ← Back to Quiz History
            </button>

            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#0F2654]"></div>
              </div>
            ) : !item ? (
              <div className="bg-white p-8 rounded-xl shadow-md border border-gray-200 text-center text-gray-600">
                Quiz history item not found.
              </div>
            ) : (
              <div className="bg-white p-6 rounded-xl shadow-md border border-gray-200">
                <h1 className="text-3xl font-bold text-[#0F2654] mb-2">
                  {item.profession || item.quiz_name || "Quiz History Item"}
                </h1>
                <p className="text-sm text-gray-500 mb-1">
                  Generated on:{" "}
                  {item.created_at
                    ? new Date(item.created_at).toLocaleString()
                    : "Unknown date"}
                </p>
                <p className="text-sm text-gray-600 mb-1">
                  Question type: {item.question_type}
                </p>
                <p className="text-sm text-gray-600 mb-1">
                  Difficulty: {item.difficulty_level || "N/A"}
                </p>
                <p className="text-sm text-gray-600 mb-4">
                  Audience: {item.audience_type || "N/A"}
                </p>
                {item.custom_instruction && (
                  <p className="text-sm text-gray-700 mb-6">
                    <strong>Custom instruction:</strong>{" "}
                    {item.custom_instruction}
                  </p>
                )}

                <div className="space-y-5">
                  {item.questions.map((question, index) => (
                    <div
                      key={index}
                      className="rounded-lg border border-gray-200 bg-gray-50 p-4"
                    >
                      <h2 className="font-semibold text-gray-800 mb-2">
                        {index + 1}. {question.question}
                      </h2>
                      {question.options && question.options.length > 0 && (
                        <ul className="list-disc list-inside text-sm text-gray-700 mb-2">
                          {question.options.map((option, optionIndex) => (
                            <li key={optionIndex}>{option}</li>
                          ))}
                        </ul>
                      )}
                      <p className="text-sm text-[#0F2654]">
                        <strong>Answer:</strong> {question.answer}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </main>
        <Footer />
      </div>
    </RequireAuth>
  );
}
