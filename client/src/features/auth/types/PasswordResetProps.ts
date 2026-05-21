export interface PasswordResetProps {
  isOpen: boolean;
  onClose: () => void;
  email?: string;
  resetMethod?: "otp" | "token";
  tokenFromUrl?: string;
  onResetSuccess: () => void;
}
