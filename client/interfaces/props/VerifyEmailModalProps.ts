export interface VerifyEmailModalProps {
  isOpen: boolean;
  onClose: () => void;
  userEmail: string;
  onVerified: () => void;
}
