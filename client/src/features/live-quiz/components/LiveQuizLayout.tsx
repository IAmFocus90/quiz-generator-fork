import React from "react";
import QuizCountdown from "./QuizCountdown";

interface LiveQuizLayoutProps {
  title: string;
  participantName?: string;
  startedAt?: string;
  timeLimitMinutes?: number;
  currentQuestion: number;
  totalQuestions: number;
  remainingSeconds: number;
  children: React.ReactNode;
}

const LiveQuizLayout: React.FC<LiveQuizLayoutProps> = ({
  title,
  participantName,
  startedAt,
  timeLimitMinutes,
  currentQuestion,
  totalQuestions,
  remainingSeconds,
  children,
}) => (
  <main className="min-h-screen bg-slate-100 px-4 py-8">
    <div className="mx-auto max-w-3xl">
      <header className="mb-5 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[#0F2654]">{title}</h1>
            <p className="mt-2 text-sm text-slate-600">
              Question {currentQuestion} of {totalQuestions}
            </p>
            {participantName && (
              <p className="mt-1 text-sm text-slate-500">
                Participant: {participantName}
              </p>
            )}
            {startedAt && (
              <p className="mt-1 text-xs text-slate-500">
                Time Started: {new Date(startedAt).toLocaleTimeString()}
              </p>
            )}
            {timeLimitMinutes && (
              <p className="mt-1 text-xs text-slate-500">
                Time Limit: {timeLimitMinutes} minutes
              </p>
            )}
          </div>
          <QuizCountdown remainingSeconds={remainingSeconds} />
        </div>
      </header>
      {children}
    </div>
  </main>
);

export default LiveQuizLayout;
