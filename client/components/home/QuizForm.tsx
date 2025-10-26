"use client";

import { useState } from "react";
import GenerateButton from "./GenerateButton";
import QuizGenerationSection from "./QuizGenerationSection";
import { useRouter } from "next/navigation";
import axios from "axios";

export default function QuizForm() {
  const [profession, setProfession] = useState("");
  const [audienceType, setAudienceType] = useState("");
  const [customInstruction, setCustomInstruction] = useState("");
  const [numQuestions, setNumQuestions] = useState(1);
  const [questionType, setQuestionType] = useState("multichoice");
  const [difficultyLevel, setDifficultyLevel] = useState("easy");
  const [token, setToken] = useState(""); // ✅ NEW
  const [errorMessage, setErrorMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleGenerateQuiz = async () => {
    if (!profession || !numQuestions || !questionType || !token) {
      setErrorMessage(
        "Please fill in the topic, number of questions, quiz type, and API token.",
      );
      return;
    }

    setLoading(true);
    setErrorMessage("");

    try {
      // ✅ Save the token first before requesting quiz generation
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/user/token`,
        { token },
      );

      const { data } = await axios.post(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/get-questions`,
        {
          profession,
          audience_type: audienceType,
          custom_instruction: customInstruction,
          num_questions: numQuestions,
          question_type: questionType,
          difficulty_level: difficultyLevel,
          token, // ✅ send token in request too (optional redundancy)
        },
      );

      console.log("🔥 RAW RESPONSE FROM BACKEND:", data);

      const userId = "userId"; // Replace with actual auth value later
      const source = data.source || "mock"; // ✅ dynamically set from backend

      const queryParams = new URLSearchParams({
        userId,
        questionType,
        numQuestions: numQuestions.toString(),
        profession,
        customInstruction,
        audienceType,
        difficultyLevel,
        source,
      }).toString();

      router.push(`/quiz_display?${queryParams}`);
    } catch (error) {
      console.error(error);
      setErrorMessage("Failed to generate quiz. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto bg-[#f7f8fa] rounded-xl p-10 shadow-lg">
      <form onSubmit={(e) => e.preventDefault()}>
        <QuizGenerationSection
          profession={profession}
          setProfession={setProfession}
          audienceType={audienceType}
          setAudienceType={setAudienceType}
          customInstruction={customInstruction}
          setCustomInstruction={setCustomInstruction}
          numQuestions={numQuestions}
          setNumQuestions={setNumQuestions}
          questionType={questionType}
          setQuestionType={setQuestionType}
          difficultyLevel={difficultyLevel}
          setDifficultyLevel={setDifficultyLevel}
          token={token} // ✅ pass token
          setToken={setToken} // ✅ pass setToken
        />
        {errorMessage && <p className="text-red-500 mb-4">{errorMessage}</p>}
        <GenerateButton onClick={handleGenerateQuiz} loading={loading} />
      </form>
    </div>
  );
}
