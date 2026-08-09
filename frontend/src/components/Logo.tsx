import React from "react";

export default function Logo({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id="dotaLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#ef4444" />
          <stop offset="50%" stopColor="#dc2626" />
          <stop offset="100%" stopColor="#991b1b" />
        </linearGradient>
        <linearGradient id="dotaGlowGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#f59e0b" />
          <stop offset="100%" stopColor="#ef4444" />
        </linearGradient>
      </defs>

      {/* Outer Shield Frame */}
      <path
        d="M20 3L35 8V20C35 29.5 28.5 35.5 20 38C11.5 35.5 5 29.5 5 20V8L20 3Z"
        fill="#0f172a"
        stroke="url(#dotaLogoGrad)"
        strokeWidth="2.5"
      />

      {/* Internal Dota 2 Diagonal Blade Bar */}
      <path
        d="M12 28L28 12"
        stroke="url(#dotaGlowGrad)"
        strokeWidth="3.5"
        strokeLinecap="round"
      />

      {/* Stats Bar Pillars */}
      <rect x="11" y="21" width="3" height="6" rx="1.5" fill="#f59e0b" />
      <rect x="16" y="16" width="3" height="11" rx="1.5" fill="#ef4444" />
      <rect x="21" y="13" width="3" height="14" rx="1.5" fill="#38bdf8" />
      <rect x="26" y="9" width="3" height="18" rx="1.5" fill="#10b981" />
    </svg>
  );
}
