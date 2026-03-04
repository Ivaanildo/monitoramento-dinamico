import { motion, useMotionValue, useTransform, animate } from "motion/react";
import { useEffect } from "react";

// 0° = north (top), clockwise positive
function polarToXY(angleDeg: number, r = 28) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: 30 + r * Math.cos(rad), y: 30 + r * Math.sin(rad) };
}

// Trail sector: from current angle, spanDeg degrees back (counter-clockwise)
function makeSector(angleDeg: number, spanDeg: number): string {
  const lead  = polarToXY(angleDeg);
  const trail = polarToXY(angleDeg - spanDeg);
  return `M 30 30 L ${lead.x.toFixed(2)} ${lead.y.toFixed(2)} A 28 28 0 0 0 ${trail.x.toFixed(2)} ${trail.y.toFixed(2)} Z`;
}

// Phosphor persistence: exponential decay in the first 110° after sweep passes
function blipAlpha(currentAngle: number, blipAngle: number): number {
  const dist = ((currentAngle - blipAngle) % 360 + 360) % 360;
  return dist < 110 ? Math.exp(-dist * 0.045) * 0.9 : 0;
}

export function RadarIcon({ size = 60 }: { size?: number }) {
  const angle = useMotionValue(0); // degrees, 0=north, clockwise+

  useEffect(() => {
    const ctrl = animate(angle, [0, 360], {
      duration: 3,
      ease: "linear",
      repeat: Infinity,
      repeatType: "loop",
    });
    return ctrl.stop;
  }, []);

  // Sweep line endpoint
  const sweepX = useTransform(angle, (a) => polarToXY(a).x);
  const sweepY = useTransform(angle, (a) => polarToXY(a).y);

  // Trail sectors — shape recomputed from real angle each frame
  const trail70 = useTransform(angle, (a) => makeSector(a, 70));
  const trail40 = useTransform(angle, (a) => makeSector(a, 40));
  const trail15 = useTransform(angle, (a) => makeSector(a, 15));

  // Blip opacities — exponential decay since sweep passed
  const blip1 = useTransform(angle, (a) => blipAlpha(a, 37));  // (42, 14) ~37°
  const blip2 = useTransform(angle, (a) => blipAlpha(a, 90));  // (50, 30) ~90°
  const blip3 = useTransform(angle, (a) => blipAlpha(a, 151)); // (40, 48) ~151°
  const blip4 = useTransform(angle, (a) => blipAlpha(a, 170)); // (33.5, 49.7) ~170°
  const blip5 = useTransform(angle, (a) => blipAlpha(a, 230)); // (17.7, 40.3) ~230°
  const blip6 = useTransform(angle, (a) => blipAlpha(a, 295)); // (8.3, 19.9)  ~295°
  const blip7 = useTransform(angle, (a) => blipAlpha(a, 340)); // (25.2, 16.8) ~340°

  return (
    <svg width={size} height={size} viewBox="0 0 60 60" fill="none">
      <defs>
        <filter id="radarGlow" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="1.4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* ── Concentric rings ── */}
      <circle cx="30" cy="30" r="28" stroke="#22c55e" strokeWidth="1.2" opacity="0.35" />
      <circle cx="30" cy="30" r="20" stroke="#22c55e" strokeWidth="1.2" opacity="0.45" />
      <circle cx="30" cy="30" r="12" stroke="#22c55e" strokeWidth="1.2" opacity="0.60" />

      {/* ── Crosshairs ── */}
      <line x1="30" y1="2"  x2="30" y2="58" stroke="#22c55e" strokeWidth="0.7" opacity="0.22" />
      <line x1="2"  y1="30" x2="58" y2="30" stroke="#22c55e" strokeWidth="0.7" opacity="0.22" />

      {/* ── Sweep trail — shape derived from real angle ── */}
      <motion.path d={trail70} fill="#22c55e" opacity={0.08} />
      <motion.path d={trail40} fill="#22c55e" opacity={0.16} />
      <motion.path d={trail15} fill="#22c55e" opacity={0.38} />

      {/* ── Sweep line — endpoint derived from real angle ── */}
      <motion.line
        x1="30" y1="30" x2={sweepX} y2={sweepY}
        stroke="#22c55e" strokeWidth="1.6" strokeLinecap="round"
        filter="url(#radarGlow)"
      />

      {/* ── Center dot ── */}
      <circle cx="30" cy="30" r="2.8" fill="#22c55e" />

      {/* ── Blips — opacity derived from angular distance to sweep ── */}
      <motion.circle cx="42"  cy="14"  r="2.5" fill="#22c55e" style={{ opacity: blip1 }} />
      <motion.circle cx="50"  cy="30"  r="2"   fill="#22c55e" style={{ opacity: blip2 }} />
      <motion.circle cx="40"  cy="48"  r="2"   fill="#22c55e" style={{ opacity: blip3 }} />
      <motion.circle cx="33.5" cy="49.7" r="1.5" fill="#22c55e" style={{ opacity: blip4 }} />
      <motion.circle cx="17.7" cy="40.3" r="2"   fill="#22c55e" style={{ opacity: blip5 }} />
      <motion.circle cx="8.3"  cy="19.9" r="1.5" fill="#22c55e" style={{ opacity: blip6 }} />
      <motion.circle cx="25.2" cy="16.8" r="2"   fill="#22c55e" style={{ opacity: blip7 }} />
    </svg>
  );
}
