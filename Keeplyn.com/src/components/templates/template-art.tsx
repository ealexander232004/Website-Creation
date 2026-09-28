import type { ReactNode } from "react";
import type { DemoSlug } from "./catalog";

/*
 * Brand illustration for the three templates. Everything is inline SVG drawn
 * in `currentColor`, so each piece inherits its template's ink and needs no
 * extra image requests or client JavaScript.
 */

const round = (n: number) => Math.round(n * 10) / 10;

function ringPath(
  cx: number,
  cy: number,
  rx: number,
  ry: number,
  scale: number,
  phase: number,
) {
  const points: string[] = [];
  for (let i = 0; i <= 72; i++) {
    const t = (i / 72) * Math.PI * 2;
    const wobble =
      1 +
      0.11 * Math.sin(3 * t + phase) +
      0.05 * Math.sin(5 * t - phase * 1.7) +
      0.03 * Math.cos(7 * t + phase * 0.6);
    const r = scale * wobble;
    points.push(`${round(cx + rx * r * Math.cos(t))} ${round(cy + ry * r * Math.sin(t))}`);
  }
  return `M${points.join("L")}Z`;
}

// Deterministic topographic survey lines: three "hills" of wobbling rings.
const CONTOURS = [
  [230, 210, 300, 200, 0.4],
  [860, 430, 380, 250, 2.1],
  [1080, 70, 230, 170, 4.2],
].flatMap(([cx, cy, rx, ry, phase]) =>
  Array.from({ length: 11 }, (_, k) =>
    ringPath(cx, cy, rx, ry, (k + 1) / 11, phase + k * 0.28),
  ),
);

export function Contours({ className = "" }: { className?: string }) {
  return (
    <svg
      className={`t-contours ${className}`}
      viewBox="0 0 1200 600"
      preserveAspectRatio="xMidYMid slice"
      fill="none"
      stroke="currentColor"
      aria-hidden="true"
    >
      {CONTOURS.map((d, i) => (
        <path key={i} d={d} vectorEffect="non-scaling-stroke" />
      ))}
    </svg>
  );
}

// An olive sprig: leaves placed along a quadratic stem.
const SPRIG = (() => {
  const p0 = [24, 262];
  const p1 = [80, 96];
  const p2 = [252, 22];
  const at = (t: number) => [
    (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0],
    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1],
  ];
  const tangent = (t: number) =>
    (Math.atan2(
      2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1]),
      2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0]),
    ) *
      180) /
    Math.PI;
  const leaves = [0.1, 0.18, 0.27, 0.35, 0.44, 0.52, 0.61, 0.69, 0.78, 0.86, 0.95].map(
    (t, i) => {
      const [x, y] = at(t);
      const side = i % 2 ? 1 : -1;
      const length = 44 - Math.abs(t - 0.5) * 30;
      return {
        transform: `translate(${round(x)} ${round(y)}) rotate(${round(tangent(t) + side * 48)})`,
        d: `M0 0Q${round(length / 2)} ${-7} ${round(length)} 0Q${round(length / 2)} 7 0 0Z`,
        vein: `M2 0H${round(length - 6)}`,
      };
    },
  );
  return {
    stem: `M${p0.join(" ")}Q${p1.join(" ")} ${p2.join(" ")}`,
    leaves,
  };
})();

export function Sprig({ className = "" }: { className?: string }) {
  return (
    <svg
      className={`t-sprig ${className}`}
      viewBox="0 0 280 280"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      aria-hidden="true"
    >
      <path d={SPRIG.stem} />
      {SPRIG.leaves.map((leaf, i) => (
        <g key={i} transform={leaf.transform}>
          <path d={leaf.d} />
          <path d={leaf.vein} opacity="0.55" />
        </g>
      ))}
      <circle cx="58" cy="162" r="7" />
      <circle cx="148" cy="62" r="6" />
    </svg>
  );
}

type GlyphKind =
  | "sun"
  | "cairn"
  | "rings"
  | "seedling"
  | "garden"
  | "landscape"
  | "asterisk"
  | "plus"
  | "smile"
  | "clock"
  | "croissant"
  | "loaf"
  | "bun"
  | "danish"
  | "coffee"
  | "cake";

const BUN_SPIRAL = (() => {
  const points: string[] = [];
  for (let i = 0; i <= 90; i++) {
    const t = (i / 90) * Math.PI * 5.2;
    const r = 1.5 + t * 1.36;
    points.push(`${round(32 + r * Math.cos(t))} ${round(33 + r * Math.sin(t) * 0.86)}`);
  }
  return `M${points.join("L")}`;
})();

const GLYPHS: Record<GlyphKind, ReactNode> = {
  sun: (
    <>
      <circle cx="32" cy="27" r="11" />
      <path d="M6 45H58M14 51H50M22 57H42" />
    </>
  ),
  cairn: (
    <>
      <ellipse cx="32" cy="49" rx="19" ry="6" />
      <ellipse cx="31" cy="36.5" rx="13" ry="5" />
      <ellipse cx="33" cy="26" rx="8" ry="4" />
      <ellipse cx="32" cy="17.5" rx="4" ry="2.5" />
      <path d="M4 57H60" />
    </>
  ),
  rings: (
    <>
      <circle cx="32" cy="32" r="24" />
      <circle cx="31" cy="32.5" r="17.5" />
      <circle cx="30" cy="33" r="11.5" />
      <circle cx="29.5" cy="33.5" r="5.5" />
      <path d="M32 8L35 22" />
    </>
  ),
  seedling: (
    <>
      <path d="M32 56V30" />
      <path d="M32 40C21 40 15 32 15 22C26 22 32 29 32 40Z" />
      <path d="M32 33C32 24 38 18 48 18C48 27 42 33 32 33Z" />
      <path d="M16 56H48" />
    </>
  ),
  garden: (
    <>
      <path d="M44 56V35" />
      <circle cx="44" cy="25" r="11" />
      <path d="M16 56C16 45 12 39 8 35M16 56C17 45 22 39 27 37M16 56V33" />
      <path d="M4 56H60" />
    </>
  ),
  landscape: (
    <>
      <path d="M2 50C14 38 25 37 35 45C44 38 53 37 62 43" />
      <path d="M2 57H62" />
      <path d="M22 41V30" />
      <circle cx="22" cy="24" r="7" />
      <circle cx="48" cy="16" r="5" />
    </>
  ),
  asterisk: <path d="M32 10V54M13 21L51 43M13 43L51 21" />,
  plus: <path d="M32 12V52M12 32H52" />,
  smile: <path d="M11 24Q32 58 53 24" />,
  clock: (
    <>
      <circle cx="32" cy="32" r="22" />
      <path d="M32 19V32L41 38" />
    </>
  ),
  croissant: (
    <>
      <path d="M5 43C9 27 21 18 32 18C43 18 55 27 59 43C53 40 47 40 43 42C39 36 25 36 21 42C17 40 11 40 5 43Z" />
      <path d="M19 25C21 30 22 36 21 42M32 18V37M45 25C43 30 42 36 43 42" />
    </>
  ),
  loaf: (
    <>
      <path d="M6 46C6 27 19 18 32 18C45 18 58 27 58 46Z" />
      <path d="M19 31L25 37M29 26L35 32M39 31L45 37" />
      <path d="M3 51H61" />
    </>
  ),
  bun: <path d={BUN_SPIRAL} />,
  danish: (
    <>
      {[0, 1, 2, 3, 4, 5].map((k) => (
        <circle
          key={k}
          cx={round(32 + 14 * Math.cos((k * Math.PI) / 3))}
          cy={round(32 + 14 * Math.sin((k * Math.PI) / 3))}
          r="9"
        />
      ))}
      <circle cx="32" cy="32" r="6" />
    </>
  ),
  coffee: (
    <>
      <path d="M12 25H46V38C46 48 38 54 29 54C20 54 12 48 12 38Z" />
      <path d="M46 29C56 29 56 43 46 41" />
      <path d="M22 17C18 13 26 11 22 6M32 17C28 13 36 11 32 6" />
      <path d="M7 59H51" />
    </>
  ),
  cake: (
    <>
      <path d="M11 31H53V55H11Z" />
      <path d="M11 35C17 40 21 33 27 37C33 41 39 33 45 37C49 40 53 35 53 35" />
      <path d="M11 45H53M32 31V19" />
      <path d="M32 15C29 12 31 8 32 6C33 8 35 12 32 15Z" />
    </>
  ),
};

export function Glyph({
  kind,
  className = "",
}: {
  kind: GlyphKind;
  className?: string;
}) {
  return (
    <svg
      className={`t-glyph t-glyph-${kind} ${className}`}
      viewBox="0 0 64 64"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {GLYPHS[kind]}
    </svg>
  );
}

const PRINCIPLE_GLYPHS: Record<DemoSlug, GlyphKind[]> = {
  moss: ["sun", "cairn", "rings"],
  northline: ["clock", "smile", "plus"],
  sera: ["bun", "danish", "coffee"],
};
const PACKAGE_GLYPHS: Record<DemoSlug, GlyphKind[]> = {
  moss: ["seedling", "garden", "landscape"],
  northline: ["smile", "asterisk", "plus"],
  sera: ["croissant", "coffee", "cake"],
};
export const MENU_GLYPHS: GlyphKind[] = ["loaf", "croissant", "bun", "danish"];

export function principleGlyph(id: DemoSlug, index: number) {
  return PRINCIPLE_GLYPHS[id][index % 3];
}
export function packageGlyph(id: DemoSlug, index: number) {
  return PACKAGE_GLYPHS[id][index % 3];
}

/** Circular type that slowly turns — Sera's sticker. */
export function SpinBadge({
  text,
  id,
  className = "",
  children,
}: {
  text: string;
  id: string;
  className?: string;
  children?: ReactNode;
}) {
  return (
    <span className={`t-spin-badge ${className}`}>
      <svg viewBox="0 0 200 200" aria-hidden="true">
        <defs>
          <path
            id={id}
            d="M100 100m-74 0a74 74 0 1 1 148 0a74 74 0 1 1-148 0"
          />
        </defs>
        <text>
          <textPath href={`#${id}`} textLength="462" lengthAdjust="spacing">
            {text}
          </textPath>
        </text>
      </svg>
      <span className="t-spin-badge-center">{children}</span>
    </span>
  );
}

/** A 90-of-120 minute dial for Northline's first visit. */
export function TimeDial({ minutes = 90 }: { minutes?: number }) {
  return (
    <svg className="t-dial" viewBox="0 0 240 240" aria-hidden="true">
      <circle className="t-dial-track" cx="120" cy="120" r="104" />
      <circle
        className="t-dial-arc"
        cx="120"
        cy="120"
        r="104"
        pathLength="120"
        strokeDasharray={`${minutes} 120`}
        transform="rotate(-90 120 120)"
      />
      {Array.from({ length: 24 }, (_, i) => (
        <line
          key={i}
          className={i % 6 === 0 ? "t-dial-tick is-major" : "t-dial-tick"}
          x1="120"
          y1={i % 6 === 0 ? 2 : 6}
          x2="120"
          y2="12"
          transform={`rotate(${i * 15} 120 120)`}
        />
      ))}
    </svg>
  );
}

function Pin({ x, y }: { x: number; y: number }) {
  return (
    <g className="t-map-pin" transform={`translate(${x} ${y})`}>
      <circle className="t-map-pulse" r="22" />
      <path d="M0 0C-10-13-15-20-15-28A15 15 0 0 1 15-28C15-20 10-13 0 0Z" />
      <circle cy="-28" r="5.5" className="t-map-pin-dot" />
    </g>
  );
}

/** Stylized, non-navigational neighborhood maps for the contact pages. */
export function TemplateMap({ id }: { id: DemoSlug }) {
  if (id === "sera")
    return (
      <svg
        className="t-map t-map-sera"
        viewBox="0 0 600 420"
        role="img"
        aria-label="Illustrated map of Exchange Street near the Portland, Maine waterfront"
      >
        <rect width="600" height="420" className="t-map-ground" />
        <rect x="392" y="74" width="148" height="92" className="t-map-park" />
        {[64, 138, 212].map((y) => (
          <path key={y} d={`M0 ${y}H600`} className="t-map-street" />
        ))}
        {[70, 150, 230, 390, 470, 550].map((x) => (
          <path key={x} d={`M${x} 0V286`} className="t-map-street" />
        ))}
        <path d="M0 262C150 256 280 270 600 250" className="t-map-street is-major" />
        <path d="M310 0V300" className="t-map-street is-feature" />
        <path
          d="M0 312C110 296 210 330 320 312C430 294 510 322 600 304V420H0Z"
          className="t-map-water"
        />
        <path
          d="M40 356C80 348 110 364 150 356M440 350C480 342 510 358 550 350"
          className="t-map-wave"
        />
        <text x="298" y="40" className="t-map-label" transform="rotate(-90 298 40)" textAnchor="end">
          Exchange St
        </text>
        <text x="30" y="252" className="t-map-label">Commercial St</text>
        <text x="466" y="126" className="t-map-label" textAnchor="middle">Park</text>
        <text x="300" y="396" className="t-map-label is-water" textAnchor="middle">Casco Bay</text>
        <Pin x={310} y={236} />
      </svg>
    );
  if (id === "northline")
    return (
      <svg
        className="t-map t-map-northline"
        viewBox="0 0 600 420"
        role="img"
        aria-label="Illustrated map of Clark Street near Lincoln Park and Lake Michigan in Chicago"
      >
        <rect width="600" height="420" className="t-map-ground" />
        {[50, 120, 190, 260, 330, 400].map((y) => (
          <path key={y} d={`M0 ${y}H600`} className="t-map-street" />
        ))}
        {[40, 110, 180, 250, 320, 390].map((x) => (
          <path key={x} d={`M${x} 0V420`} className="t-map-street" />
        ))}
        <rect x="266" y="24" width="170" height="150" rx="6" className="t-map-park" />
        <path
          d="M410 0C394 70 424 132 408 200C394 264 432 332 422 420H600V0Z"
          className="t-map-water"
        />
        <path d="M140 0L400 420" className="t-map-street is-feature" />
        <text x="184" y="45" className="t-map-label" transform="rotate(58.2 184 45)">
          Clark St
        </text>
        <text x="338" y="104" className="t-map-label" textAnchor="middle">Lincoln Park</text>
        <text x="508" y="226" className="t-map-label is-water" textAnchor="middle">Lake Michigan</text>
        <Pin x={270} y={210} />
      </svg>
    );
  return (
    <svg
      className="t-map t-map-moss"
      viewBox="0 0 600 420"
      role="img"
      aria-label="Illustrated service map linking Austin, Dripping Springs, and San Antonio"
    >
      <rect width="600" height="420" className="t-map-ground" />
      <g className="t-map-contours">
        {CONTOURS.slice(0, 22).map((d, i) => (
          <path key={i} d={d} transform="scale(0.5)" />
        ))}
      </g>
      <path
        d="M0 300C90 290 150 252 230 262C310 272 360 232 440 216C500 204 560 172 600 152"
        className="t-map-river"
      />
      <ellipse cx="300" cy="220" rx="232" ry="140" className="t-map-area" />
      <path d="M440 150C380 160 320 170 270 180C224 228 196 276 172 318" className="t-map-route" />
      {(
        [
          [440, 150, "Austin", "start"],
          [270, 180, "Dripping Springs", "end"],
          [172, 318, "San Antonio", "start"],
        ] as const
      ).map(([x, y, label, anchor]) => (
        <g key={label}>
          <circle cx={x} cy={y} r="11" className="t-map-halo" />
          <circle cx={x} cy={y} r="4.5" className="t-map-city" />
          <text
            x={anchor === "end" ? x - 20 : x + 20}
            y={y + 6}
            textAnchor={anchor}
            className="t-map-label"
          >
            {label}
          </text>
        </g>
      ))}
    </svg>
  );
}

/** Seamless ticker. The second copy is decorative and hidden from assistive tech. */
export function Marquee({
  children,
  className = "",
  decorative = false,
}: {
  children: ReactNode;
  className?: string;
  decorative?: boolean;
}) {
  return (
    <div className={`t-marquee ${className}`} aria-hidden={decorative || undefined}>
      <div className="t-marquee-track">
        <div className="t-marquee-group">{children}</div>
        <div className="t-marquee-group" aria-hidden="true">
          {children}
        </div>
      </div>
    </div>
  );
}
