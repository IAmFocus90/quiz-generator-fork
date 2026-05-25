import Link from "next/link";
import React from "react";

interface GuestSignupPopupProps {
  isOpen: boolean;
  onClose: () => void;
}

const GuestSignupPopup: React.FC<GuestSignupPopupProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div className="w-full max-w-md rounded-md bg-white p-6 shadow-xl">
        <h2 className="text-xl font-bold text-[#0F2654]">
          Create your free Quiz Generator account
        </h2>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Create an account to generate your own quizzes, save your results, and
          track your progress.
        </p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Link
            href="/auth/register"
            className="rounded-md bg-[#0a3264] px-4 py-2 text-center text-sm font-semibold text-white hover:bg-[#082952]"
          >
            Create Account
          </Link>
          <Link
            href="/auth/login"
            className="rounded-md border border-slate-300 px-4 py-2 text-center text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Login
          </Link>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
          >
            Maybe Later
          </button>
        </div>
      </div>
    </div>
  );
};

export default GuestSignupPopup;
