import { useRouter } from "next/router";
import React, { FormEvent, useState } from "react";
import toast from "react-hot-toast";
import { NavBar, Footer } from "../../components/home";
import { liveQuizService } from "../../src/services/liveQuizService";

const QuizAccessPage = () => {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const normalizedCode = code.trim().toUpperCase();
    if (!normalizedCode) {
      toast.error("Enter an access code.");
      return;
    }

    try {
      setIsLoading(true);
      await liveQuizService.validateAccessCode(normalizedCode);
      router.push(`/quiz-access/${encodeURIComponent(normalizedCode)}`);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Invalid access code.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-100">
      <NavBar />
      <main className="flex flex-1 items-center justify-center px-4 py-10">
        <form
          onSubmit={handleSubmit}
          className="w-full max-w-md rounded-md border border-slate-200 bg-white p-6 shadow-sm"
        >
          <h1 className="text-2xl font-bold text-[#0F2654]">
            Enter live quiz access code
          </h1>
          <label className="mt-6 block text-sm font-semibold text-slate-700">
            Access code
          </label>
          <input
            value={code}
            onChange={(event) => setCode(event.target.value.toUpperCase())}
            className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-lg tracking-widest outline-none focus:border-[#0a3264] focus:ring-2 focus:ring-blue-100"
            autoComplete="off"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="mt-6 w-full rounded-md bg-[#0a3264] px-4 py-2 text-sm font-semibold text-white hover:bg-[#082952] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoading ? "Checking..." : "Continue"}
          </button>
        </form>
      </main>
      <Footer />
    </div>
  );
};

export default QuizAccessPage;
