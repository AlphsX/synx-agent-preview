import React, { useState, useEffect } from "react";
import { useIdleDetection } from "@/hooks/useIdleDetection";
import { Meteors } from "./meteors";

interface IdleMeteorAnimationProps {
  showWelcome: boolean; // only show when welcome screen is visible
}

/**
 * Orchestration component that displays falling meteor animation during idle periods
 * Activates after 15 seconds of user inactivity
 * Meteors fall continuously from top to bottom until user moves cursor
 * Only renders when the welcome screen is visible and user is idle
 * Respects user's motion preferences for accessibility
 */
export const IdleMeteorAnimation: React.FC<IdleMeteorAnimationProps> = ({
  showWelcome,
}) => {
  const { isIdle } = useIdleDetection({ idleTime: 15000 }); // ms
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  // Check for prefers-reduced-motion preference
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

    // Set initial value
    setPrefersReducedMotion(mediaQuery.matches);

    // Listen for changes
    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    // Use modern addEventListener (supported in all modern browsers)
    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  // Don't render if user prefers reduced motion
  if (prefersReducedMotion) {
    return null;
  }

  // Only render meteors when welcome screen is visible AND user is idle
  if (!showWelcome || !isIdle) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 pointer-events-none z-10 transition-opacity duration-500 opacity-100 overflow-hidden"
      aria-hidden="true"
    >
      <Meteors number={30} />
    </div>
  );
};
