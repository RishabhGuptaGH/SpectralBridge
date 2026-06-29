export default function Background() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 bg-canvas-base" />

      {/* subtle green + cyan ambient glows (replaces the old purple ones) */}
      <div className="absolute -top-48 left-1/4 h-[34rem] w-[34rem] -translate-x-1/2 rounded-full bg-accent/10 blur-[130px] animate-glowPulse" />
      <div
        className="absolute bottom-0 right-0 h-[30rem] w-[30rem] rounded-full bg-bridge/10 blur-[130px] animate-glowPulse"
        style={{ animationDelay: "2.5s" }}
      />

      {/* fine engineering grid, faint, masked toward the top */}
      <div
        className="absolute inset-0 opacity-[0.5]"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(139,148,158,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(139,148,158,0.06) 1px, transparent 1px)",
          backgroundSize: "44px 44px",
          maskImage: "radial-gradient(ellipse 75% 55% at 50% 25%, black 35%, transparent 100%)",
          WebkitMaskImage: "radial-gradient(ellipse 75% 55% at 50% 25%, black 35%, transparent 100%)",
        }}
      />

      {/* a thin top accent line, like an editor status bar */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-accent/40 to-transparent" />
    </div>
  );
}
