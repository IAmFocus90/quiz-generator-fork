import { useRouter } from "next/router";
import { logoutUser } from "../lib/functions/auth";

export const useLogout = () => {
  const router = useRouter();

  const logout = async () => {
    const token = localStorage.getItem("accessToken");
    if (!token) {
      router.push("/auth/login");
      return;
    }

    // try {
    //   await logoutUser(token);
    // } catch (error) {
    //   console.error("Backend logout failed, clearing token anyway:", error);
    // } finally {
    //   localStorage.removeItem("accessToken");
    //   router.push("/auth/login");
    // }
  };

  return { logout };
};
