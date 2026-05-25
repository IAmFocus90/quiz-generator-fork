export interface RequestPasswordResetProps {
  isOpen: boolean;
  onClose: () => void;
  onRequestSuccess: (email: string) => void;
}
