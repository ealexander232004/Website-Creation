type VisualProps = {
  className?: string;
};

type MossVinesProps = VisualProps & {
  variant?: "hero" | "canopy" | "thread";
};

export function MossVines({ className = "", variant = "hero" }: MossVinesProps) {
  return (
    <svg
      className={`moss-vines moss-vines-${variant} ${className}`}
      viewBox="0 0 1200 800"
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
    >
      <g className="moss-vine-shadow">
        <path d="M-60 740 C180 680 90 390 350 354 C598 320 520 118 812 148 C1010 168 1024 28 1260 54" />
        <path d="M180 860 C188 614 438 660 462 436 C488 214 706 330 766 88 C802 -58 1020 16 1160 -84" />
        <path d="M-120 168 C128 128 198 286 416 228 C674 158 772 438 1006 330 C1110 282 1190 314 1290 454" />
      </g>
      <g className="moss-vine-stem">
        <path pathLength="1" d="M-60 740 C180 680 90 390 350 354 C598 320 520 118 812 148 C1010 168 1024 28 1260 54" />
        <path pathLength="1" d="M180 860 C188 614 438 660 462 436 C488 214 706 330 766 88 C802 -58 1020 16 1160 -84" />
        <path pathLength="1" d="M-120 168 C128 128 198 286 416 228 C674 158 772 438 1006 330 C1110 282 1190 314 1290 454" />
      </g>
      <g className="moss-vine-tendril">
        <path pathLength="1" d="M348 354 C292 274 314 214 392 198 C456 186 482 248 442 286 C410 314 368 298 374 260" />
        <path pathLength="1" d="M766 88 C702 44 698 -12 748 -42 C804 -76 866 -34 850 18 C840 52 804 58 788 34" />
        <path pathLength="1" d="M1006 330 C946 408 978 474 1048 480 C1110 486 1130 424 1088 394 C1056 372 1022 390 1028 420" />
      </g>
      <g className="moss-vine-leaves">
        <ellipse cx="124" cy="640" rx="22" ry="52" transform="rotate(-46 124 640)" />
        <ellipse cx="198" cy="486" rx="18" ry="45" transform="rotate(28 198 486)" />
        <ellipse cx="350" cy="354" rx="22" ry="54" transform="rotate(78 350 354)" />
        <ellipse cx="512" cy="286" rx="20" ry="48" transform="rotate(-36 512 286)" />
        <ellipse cx="646" cy="164" rx="18" ry="45" transform="rotate(44 646 164)" />
        <ellipse cx="836" cy="152" rx="23" ry="56" transform="rotate(-62 836 152)" />
        <ellipse cx="1012" cy="112" rx="18" ry="46" transform="rotate(34 1012 112)" />
        <ellipse cx="267" cy="636" rx="18" ry="44" transform="rotate(64 267 636)" />
        <ellipse cx="462" cy="436" rx="23" ry="54" transform="rotate(-54 462 436)" />
        <ellipse cx="622" cy="316" rx="17" ry="42" transform="rotate(72 622 316)" />
        <ellipse cx="906" cy="12" rx="20" ry="50" transform="rotate(46 906 12)" />
        <ellipse cx="202" cy="216" rx="20" ry="50" transform="rotate(-58 202 216)" />
        <ellipse cx="416" cy="228" rx="23" ry="56" transform="rotate(34 416 228)" />
        <ellipse cx="682" cy="272" rx="18" ry="44" transform="rotate(-32 682 272)" />
        <ellipse cx="884" cy="372" rx="20" ry="50" transform="rotate(64 884 372)" />
        <ellipse cx="1102" cy="326" rx="18" ry="46" transform="rotate(-46 1102 326)" />
      </g>
      <g className="moss-vine-sparks">
        <circle cx="350" cy="354" r="8" /><circle cx="766" cy="88" r="8" />
        <circle cx="1006" cy="330" r="8" /><circle cx="462" cy="436" r="8" />
      </g>
    </svg>
  );
}

export function NorthlineSignalMap({ className = "" }: VisualProps) {
  return (
    <svg className={`northline-signal-map ${className}`} viewBox="0 0 800 520" aria-hidden="true" focusable="false">
      <g className="northline-signal-rings">
        <ellipse cx="400" cy="260" rx="296" ry="128" />
        <ellipse cx="400" cy="260" rx="224" ry="194" transform="rotate(28 400 260)" />
        <ellipse cx="400" cy="260" rx="136" ry="268" transform="rotate(-54 400 260)" />
      </g>
      <path className="northline-signal-line" pathLength="1" d="M42 330 C136 330 132 186 230 186 S312 366 410 366 S492 128 594 128 S650 274 762 274" />
      <g className="northline-signal-nodes">
        <circle cx="42" cy="330" r="11" /><circle cx="230" cy="186" r="14" />
        <circle cx="410" cy="366" r="11" /><circle cx="594" cy="128" r="14" />
        <circle cx="762" cy="274" r="11" />
      </g>
      <g className="northline-signal-cross"><path d="M376 260h48M400 236v48" /></g>
    </svg>
  );
}

export function SeraProofingField({ className = "" }: VisualProps) {
  return (
    <svg className={`sera-proofing-field ${className}`} viewBox="0 0 900 560" aria-hidden="true" focusable="false">
      <g className="sera-proof-rays">
        {Array.from({ length: 18 }, (_, index) => (
          <path key={index} d="M450 280V18" transform={`rotate(${index * 20} 450 280)`} />
        ))}
      </g>
      <g className="sera-proof-orbits">
        <circle cx="450" cy="280" r="190" /><circle cx="450" cy="280" r="124" /><circle cx="450" cy="280" r="60" />
      </g>
      <path className="sera-proof-score" pathLength="1" d="M186 338 C278 218 366 392 456 270 C548 146 630 326 724 208" />
      <g className="sera-proof-bubbles">
        <circle cx="222" cy="178" r="18" /><circle cx="320" cy="420" r="12" /><circle cx="548" cy="96" r="16" />
        <circle cx="682" cy="402" r="22" /><circle cx="766" cy="164" r="10" />
      </g>
      <circle className="sera-proof-core" cx="450" cy="280" r="37" />
    </svg>
  );
}
