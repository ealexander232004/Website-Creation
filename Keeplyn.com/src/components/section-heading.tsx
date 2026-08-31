interface SectionHeadingProps {
  eyebrow: string;
  title: string;
  description?: string;
  align?: "left" | "center";
  inverse?: boolean;
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  align = "left",
  inverse = false,
}: SectionHeadingProps) {
  return (
    <div className={align === "center" ? "mx-auto max-w-3xl text-center" : "max-w-3xl"}>
      <p
        className={`mb-6 font-mono text-[10px] uppercase tracking-[0.18em] ${
          inverse ? "text-mint" : "text-violet"
        }`}
      >
        {eyebrow}
      </p>
      <h2
        className={`text-balance text-4xl font-semibold leading-[0.98] tracking-[-0.06em] sm:text-5xl lg:text-6xl ${
          inverse ? "text-white" : "text-navy"
        }`}
      >
        {title}
      </h2>
      {description ? (
        <p
          className={`mt-6 max-w-2xl text-pretty text-base leading-7 sm:text-lg ${
            inverse ? "text-white/65" : "text-slate"
          }`}
        >
          {description}
        </p>
      ) : null}
    </div>
  );
}
