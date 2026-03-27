import { useRouter } from "next/router";
import NavBar from "../../components/home/NavBar";
import Footer from "../../components/home/Footer";
import { ROUTES } from "../../constants/patterns/routes";

export default function VerifyEmailNoticePage() {
  const router = useRouter();

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <NavBar />
      <main className="mx-auto flex w-full max-w-3xl flex-1 items-center px-4 py-10">
        <section className="w-full rounded-2xl border border-amber-200 bg-white p-8 shadow-sm">
          <h1 className="text-2xl font-bold text-[#143E6F]">
            Verify your email to continue
          </h1>
          <p className="mt-3 text-gray-700">
            We sent a verification email to your inbox. Open it and use either
            the code or link to verify your account.
          </p>
          <p className="mt-2 text-sm text-gray-600">
            After verification, come back and retry your action.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => router.push(ROUTES.VERIFY_EMAIL)}
              className="rounded-lg bg-[#143E6F] px-4 py-2 font-semibold text-white transition hover:bg-[#0f2f54]"
            >
              Open Verification Page
            </button>
            <button
              type="button"
              onClick={() => router.push("/")}
              className="rounded-lg border border-gray-300 px-4 py-2 font-semibold text-gray-700 transition hover:bg-gray-100"
            >
              Back Home
            </button>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
