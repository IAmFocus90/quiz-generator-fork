import React, { FormEvent, useState } from "react";
import toast from "react-hot-toast";
import { TokenService } from "@shared/auth/tokenService";
import { liveQuizService } from "@features/live-quiz/api/liveQuizService";

interface LiveQuizAccessCodePanelProps {
  quizId?: string;
}

const tomorrowLocalValue = () => {
  const date = new Date(Date.now() + 24 * 60 * 60 * 1000);
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
};

const LiveQuizAccessCodePanel: React.FC<LiveQuizAccessCodePanelProps> = ({
  quizId,
}) => {
  const [duration, setDuration] = useState(20);
  const [expiresAt, setExpiresAt] = useState(tomorrowLocalValue());
  const [accessCode, setAccessCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  if (!quizId || !TokenService.hasTokens()) return null;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      setIsLoading(true);
      const response = await liveQuizService.createAccessCode({
        quizId,
        time_limit_minutes: duration,
        access_code_expires_at: new Date(expiresAt).toISOString(),
      });
      setAccessCode(response.access_code);
      toast.success("Live quiz access code generated.");
    } catch (error: any) {
      toast.error(
        error?.response?.data?.detail || "Could not generate access code.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const accessUrl =
    typeof window !== "undefined" && accessCode
      ? `${window.location.origin}/quiz-access/${accessCode}`
      : "";

  return (
    <section className="rounded-md border border-slate-200 bg-white px-4 py-5 shadow-sm">
      <h2 className="text-lg font-bold text-[#0F2654]">Live Quiz Mode</h2>
      <form
        onSubmit={handleSubmit}
        className="mt-4 grid gap-4 md:grid-cols-[1fr_1fr_auto]"
      >
        <label className="block text-sm font-semibold text-slate-700">
          Duration minutes
          <input
            type="number"
            min={1}
            max={1440}
            value={duration}
            onChange={(event) => setDuration(Number(event.target.value))}
            className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-[#0a3264] focus:ring-2 focus:ring-blue-100"
          />
        </label>
        <label className="block text-sm font-semibold text-slate-700">
          Access code expires
          <input
            type="datetime-local"
            value={expiresAt}
            onChange={(event) => setExpiresAt(event.target.value)}
            className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-[#0a3264] focus:ring-2 focus:ring-blue-100"
          />
        </label>
        <button
          type="submit"
          disabled={isLoading}
          className="self-end rounded-md bg-[#0a3264] px-4 py-2 text-sm font-semibold text-white hover:bg-[#082952] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? "Generating..." : "Generate Code"}
        </button>
      </form>

      {accessCode && (
        <div className="mt-4 rounded-md bg-slate-50 p-4">
          <p className="text-sm font-semibold text-slate-600">Access code</p>
          <p className="mt-1 text-2xl font-bold tracking-widest text-[#0F2654]">
            {accessCode}
          </p>
          <button
            type="button"
            onClick={() => {
              navigator.clipboard.writeText(accessUrl);
              toast.success("Live quiz link copied.");
            }}
            className="mt-3 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-white"
          >
            Copy Link
          </button>
        </div>
      )}
    </section>
  );
};

export default LiveQuizAccessCodePanel;
