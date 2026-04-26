export function Logo({ size = 22 }: { size?: number }) {
  return (
    <span className="inline-flex items-center gap-2">
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden
      >
        <circle cx="12" cy="12" r="10.5" stroke="currentColor" strokeWidth="1.2" />
        <path
          d="M5 14 L9.5 9 L13 12.5 L19 6.5"
          stroke="currentColor"
          strokeWidth="1.4"
          fill="none"
          strokeLinecap="round"
        />
        <circle cx="19" cy="6.5" r="1.5" fill="currentColor" />
      </svg>
      <span className="serif" style={{ fontSize: size * 0.95, lineHeight: 1 }}>
        UnderwriteAI
      </span>
    </span>
  );
}
