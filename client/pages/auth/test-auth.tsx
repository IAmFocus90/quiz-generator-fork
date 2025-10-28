import { useState } from "react";
import {
  registerUser,
  verifyOtp,
  verifyLink,
  resendVerification,
  loginUser,
  getProfile,
  requestPasswordReset,
  resetPassword,
  logoutUser,
} from "../lib/api/auth";

const TestAuthPage: React.FC = () => {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [token, setToken] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [authToken, setAuthToken] = useState<string>("");

  const handleRegister = async () => {
    try {
      const res = await registerUser({ email, username, password });
      setMessage(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setMessage(err.response?.data || err.message);
    }
  };

  const handleVerifyOtp = async () => {
    try {
      const res = await verifyOtp(email, otp);
      setMessage(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setMessage(err.response?.data || err.message);
    }
  };

  const handleVerifyLink = async () => {
    try {
      const res = await verifyLink(token);
      setMessage(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setMessage(err.response?.data || err.message);
    }
  };

  const handleResendVerification = async () => {
    try {
      const res = await resendVerification(email);
      setMessage(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setMessage(err.response?.data || err.message);
    }
  };

  const handleLogin = async () => {
    try {
      const res = await loginUser({ identifier: email, password });
      setMessage(JSON.stringify(res.data, null, 2));
      if (res.data?.access_token) setAuthToken(res.data.access_token);
    } catch (err: any) {
      setMessage(err.response?.data || err.message);
    }
  };

  const handleGetProfile = async () => {
    try {
      const res = await getProfile(authToken);
      setMessage(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setMessage(err.response?.data || err.message);
    }
  };

  const handleRequestPasswordReset = async () => {
    try {
      const res = await requestPasswordReset(email);
      setMessage(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setMessage(err.response?.data || err.message);
    }
  };

  const handleResetPassword = async () => {
    try {
      const res = await resetPassword({ token, new_password: password });
      setMessage(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setMessage(err.response?.data || err.message);
    }
  };

  const handleLogout = async () => {
    try {
      const res = await logoutUser(authToken);
      setMessage(JSON.stringify(res.data, null, 2));
      setAuthToken("");
    } catch (err: any) {
      setMessage(err.response?.data || err.message);
    }
  };

  return (
    <div className="min-h-screen p-8 bg-gray-100">
      <h1 className="text-2xl font-bold mb-4 text-[#143E6F]">Test Auth API</h1>

      {/* Inputs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <input
          type="text"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="px-3 py-2 border rounded"
        />
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="px-3 py-2 border rounded"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="px-3 py-2 border rounded"
        />
        <input
          type="text"
          placeholder="OTP"
          value={otp}
          onChange={(e) => setOtp(e.target.value)}
          className="px-3 py-2 border rounded"
        />
        <input
          type="text"
          placeholder="Token"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className="px-3 py-2 border rounded"
        />
      </div>

      {/* Buttons */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <button
          onClick={handleRegister}
          className="bg-[#143E6F] text-white py-2 rounded"
        >
          Register
        </button>
        <button
          onClick={handleVerifyOtp}
          className="bg-[#143E6F] text-white py-2 rounded"
        >
          Verify OTP
        </button>
        <button
          onClick={handleVerifyLink}
          className="bg-[#143E6F] text-white py-2 rounded"
        >
          Verify Link
        </button>
        <button
          onClick={handleResendVerification}
          className="bg-[#143E6F] text-white py-2 rounded"
        >
          Resend Verification
        </button>
        <button
          onClick={handleLogin}
          className="bg-[#143E6F] text-white py-2 rounded"
        >
          Login
        </button>
        <button
          onClick={handleGetProfile}
          className="bg-[#143E6F] text-white py-2 rounded"
        >
          Profile
        </button>
        <button
          onClick={handleRequestPasswordReset}
          className="bg-[#143E6F] text-white py-2 rounded"
        >
          Request Reset
        </button>
        <button
          onClick={handleResetPassword}
          className="bg-[#143E6F] text-white py-2 rounded"
        >
          Reset Password
        </button>
        <button
          onClick={handleLogout}
          className="bg-[#143E6F] text-white py-2 rounded"
        >
          Logout
        </button>
      </div>

      {/* Output */}
      <pre className="bg-white p-4 rounded shadow overflow-x-auto">
        {message}
      </pre>
    </div>
  );
};

export default TestAuthPage;
