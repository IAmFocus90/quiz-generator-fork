import { useEffect, useRef, useState } from "react";

export const useLiveQuizTimer = (
  expiresAt?: string,
  serverNow?: string,
  initialRemainingSeconds = 0,
  onExpire?: () => void,
  isRunning = true,
) => {
  const [remainingSeconds, setRemainingSeconds] = useState(
    initialRemainingSeconds,
  );
  const didExpireRef = useRef(false);
  const onExpireRef = useRef(onExpire);

  useEffect(() => {
    onExpireRef.current = onExpire;
  }, [onExpire]);

  useEffect(() => {
    setRemainingSeconds(Math.max(0, initialRemainingSeconds));
  }, [initialRemainingSeconds]);

  useEffect(() => {
    if (!expiresAt || !isRunning) return;

    const expiresAtMs = new Date(expiresAt).getTime();
    const serverNowMs = serverNow ? new Date(serverNow).getTime() : NaN;
    if (!Number.isFinite(expiresAtMs)) {
      return;
    }

    didExpireRef.current = false;
    const serverOffsetMs = Number.isFinite(serverNowMs)
      ? serverNowMs - Date.now()
      : 0;

    const calculateRemaining = () => {
      const adjustedNow = Date.now() + serverOffsetMs;
      const remaining = Math.max(
        0,
        Math.floor((expiresAtMs - adjustedNow) / 1000),
      );
      setRemainingSeconds(remaining);
      if (remaining === 0 && !didExpireRef.current) {
        didExpireRef.current = true;
        onExpireRef.current?.();
      }
    };

    calculateRemaining();
    const intervalId = window.setInterval(calculateRemaining, 1000);
    return () => window.clearInterval(intervalId);
  }, [expiresAt, serverNow, isRunning]);

  return remainingSeconds;
};
