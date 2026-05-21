"use client";

import React from "react";
import NavBar from "@features/quiz/components/NavBar";
import QuizForm from "@features/quiz/components/QuizForm";
import Footer from "@features/quiz/components/Footer";

export default function QuizPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <NavBar />

      <main className="flex-grow px-4 sm:px-6 md:px-8 py-6">
        <div className="max-w-screen-md mx-auto w-full">
          <QuizForm />
        </div>
      </main>

      <Footer />
    </div>
  );
}
