import { useState, useEffect } from "react";
import { SignUpModalProps } from "../../interfaces/props/sign-up-modal-props";
import { registerUser } from "../../lib";
import { EMAIL_REGEX, PASSWORD_REGEX } from "../../constants/patterns/patterns";
import { useRouter } from "next/router";
import { ROUTES } from "../../constants/patterns/routes";
import VerifyEmailModal from "./VerifyEmailModal";

interface ExtendedSignUpModalProps extends SignUpModalProps {
  onSuccess?: () => void;
}

export default function SignUpModal({
  isOpen,
  onClose,
  switchToSignIn,
  onSuccess,
}: ExtendedSignUpModalProps) {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [passwordStrength, setPasswordStrength] = useState("");

  // ✅ Nouveaux états pour gérer le modal de vérification
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState("");

  useEffect(() => {
    const newErrors: Record<string, string> = {};

    if (username && username.length < 3) {
      newErrors.username = "Username must be at least 3 characters.";
    }

    if (fullName && fullName.length < 3) {
      newErrors.fullName = "Full name must be at least 3 characters.";
    }

    if (email && !EMAIL_REGEX.test(email)) {
      newErrors.email = "Please enter a valid email address.";
    }

    if (password && !PASSWORD_REGEX.test(password)) {
      newErrors.password =
        "Password must be at least 8 characters long, include a number, a letter, and a special character.";
    }

    if (confirmPassword && password !== confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match.";
    }

    setErrors(newErrors);
  }, [username, fullName, email, password, confirmPassword]);

  useEffect(() => {
    if (!password) {
      setPasswordStrength("");
      return;
    }

    let score = 0;
    if (password.length >= 8) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    if (score <= 1) setPasswordStrength("Weak");
    else if (score === 2) setPasswordStrength("Fair");
    else if (score === 3) setPasswordStrength("Good");
    else setPasswordStrength("Strong");
  }, [password]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (Object.keys(errors).length > 0) return;

    try {
      setLoading(true);
      await registerUser({
        username,
        email,
        full_name: fullName,
        password,
      });

      // ✅ Après inscription réussie, stocker l'email et ouvrir le modal de vérification
      setRegisteredEmail(email);
      // onClose(); // Fermer le modal d'inscription
      setShowVerifyModal(true); // Ouvrir le modal de vérification

      // ✅ Réinitialiser les champs du formulaire
      setUsername("");
      setFullName("");
      setEmail("");
      setPassword("");
      setConfirmPassword("");
      setErrors({});
      setPasswordStrength("");
    } catch (error: any) {
      console.error("Registration error:", error);
      setErrors({
        global:
          error.response?.data?.detail ||
          "Registration failed. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const getStrengthColor = () => {
    switch (passwordStrength) {
      case "Weak":
        return "text-red-600";
      case "Fair":
        return "text-yellow-600";
      case "Good":
        return "text-blue-600";
      case "Strong":
        return "text-green-600";
      default:
        return "text-gray-400";
    }
  };

  return (
    <>
      {/* Modal d'inscription */}
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="bg-white rounded-2xl w-full max-w-md p-8">
          <div className="relative">
            <h2 className="text-2xl font-semibold text-center text-[#143E6F] font-serif mb-6">
              Sign Up
            </h2>
            <button
              onClick={onClose}
              className="absolute top-0 right-0 text-gray-400 hover:text-gray-600 text-2xl"
            >
              &times;
            </button>
          </div>

          {errors.global && (
            <div className="bg-red-50 border border-red-200 text-red-600 text-sm p-3 rounded-md mb-4">
              {errors.global}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Username */}
            <div className="mb-4">
              <label
                className="block text-sm font-medium mb-2"
                htmlFor="username"
              >
                Choose a Username
              </label>
              <input
                type="text"
                id="username"
                placeholder="Enter Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className={`w-full px-4 py-2 border rounded-md ${
                  errors.username ? "border-red-500" : "border-gray-300"
                }`}
                required
              />
              {errors.username && (
                <p className="text-red-600 text-sm mt-1">{errors.username}</p>
              )}
            </div>

            {/* Full Name */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2" htmlFor="name">
                Full Name
              </label>
              <input
                type="text"
                id="name"
                placeholder="Enter Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className={`w-full px-4 py-2 border rounded-md ${
                  errors.fullName ? "border-red-500" : "border-gray-300"
                }`}
                required
              />
              {errors.fullName && (
                <p className="text-red-600 text-sm mt-1">{errors.fullName}</p>
              )}
            </div>

            {/* Email */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2" htmlFor="email">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                placeholder="Enter Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={`w-full px-4 py-2 border rounded-md ${
                  errors.email ? "border-red-500" : "border-gray-300"
                }`}
                required
              />
              {errors.email && (
                <p className="text-red-600 text-sm mt-1">{errors.email}</p>
              )}
            </div>

            {/* Password */}
            <div className="mb-4">
              <label
                className="block text-sm font-medium mb-2"
                htmlFor="password"
              >
                Password
              </label>
              <input
                type="password"
                id="password"
                placeholder="Enter Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`w-full px-4 py-2 border rounded-md ${
                  errors.password ? "border-red-500" : "border-gray-300"
                }`}
                required
              />
              {errors.password && (
                <p className="text-red-600 text-sm mt-1">{errors.password}</p>
              )}
              {password && (
                <p className={`text-sm mt-1 ${getStrengthColor()}`}>
                  Strength: {passwordStrength}
                </p>
              )}
            </div>

            {/* Confirm Password */}
            <div className="mb-6">
              <label
                className="block text-sm font-medium mb-2"
                htmlFor="confirmPassword"
              >
                Confirm Password
              </label>
              <input
                type="password"
                id="confirmPassword"
                placeholder="Confirm Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={`w-full px-4 py-2 border rounded-md ${
                  errors.confirmPassword ? "border-red-500" : "border-gray-300"
                }`}
                required
              />
              {errors.confirmPassword && (
                <p className="text-red-600 text-sm mt-1">
                  {errors.confirmPassword}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || Object.keys(errors).length > 0}
              className="w-full bg-[#143E6F] text-white py-2 rounded-md font-medium mb-6 disabled:opacity-50 hover:bg-[#0f2f54] transition-colors"
            >
              {loading ? "Signing Up..." : "Sign Up"}
            </button>
          </form>

          {/* Login Redirect */}
          <div className="text-center mt-6 text-sm">
            Already Have An Account?{" "}
            <button
              onClick={() => {
                onClose();
                switchToSignIn();
                router.push(ROUTES.LOGIN);
              }}
              className="text-gray-400 hover:text-gray-600 underline"
            >
              Login
            </button>
          </div>
        </div>
      </div>

      {/* ✅ Modal de vérification d'email (s'ouvre après inscription réussie) */}
      <VerifyEmailModal
        isOpen={showVerifyModal}
        onClose={() => {
          setShowVerifyModal(false);
          onClose(); // now it is safe to close SignUpModal
        }}
        userEmail={registeredEmail}
        onVerified={() => {
          setShowVerifyModal(false);
          if (onSuccess) onSuccess();
          else router.push(ROUTES.LOGIN);
        }}
      />
    </>
  );
}
