"use client";

import React, { useState } from "react";
import { saveQuiz } from "../../lib/functions/savedQuiz";

interface SaveQuizButtonProps {
  quizData: any;
  userId?: string;
}

export default function SaveQuizButton({
  quizData,
  userId = "dummy-user-123",
}: SaveQuizButtonProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [quizTitle, setQuizTitle] = useState("");
  const [showInput, setShowInput] = useState(false);

  const handleSaveQuiz = async () => {
    if (!quizTitle) {
      alert("Please enter a title for your quiz");
      return;
    }
    try {
      setIsSaving(true);
      await saveQuiz(quizTitle, quizData);
      alert("Quiz saved successfully!");
      setShowInput(false);
      setQuizTitle("");
    } catch (err) {
      console.error("Error saving quiz:", err);
      alert("Failed to save quiz");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="mt-4">
      {!showInput ? (
        <button
          onClick={() => setShowInput(true)}
          className="bg-[#0a3264] hover:bg-[#082952] text-white font-semibold px-4 py-2 rounded-xl shadow-md transition text-sm"
        >
          Save Quiz
        </button>
      ) : (
        <div className="flex flex-col gap-2">
          <input
            type="text"
            placeholder="Enter quiz title"
            value={quizTitle}
            onChange={(e) => setQuizTitle(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2 w-full text-sm"
          />
          <button
            onClick={handleSaveQuiz}
            disabled={isSaving}
            className="bg-[#0a3264] hover:bg-[#082952] text-white font-semibold px-4 py-2 rounded-xl shadow-md transition text-sm disabled:bg-gray-400"
          >
            {isSaving ? "Saving..." : "Confirm Save"}
          </button>
        </div>
      )}
    </div>
  );
}
