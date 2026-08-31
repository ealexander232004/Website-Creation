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
    <div className={align === "center" ? "mx-auto max-w-2xl text-center" : "max-w-2xl"}>
      <p
        className={`mb-4 text-xs font-bold uppercase tracking-[0.18em] ${
          inverse ? "text-mint" : "text-violet"
        }`}
      >
        {eyebrow}
      </p>
      <h2
        className={`text-balance text-3xl font-bold tracking-[-0.045em] sm:text-4xl lg:text-5xl ${
          inverse ? "text-white" : "text-navy"
        }`}
      >
        {title}
      </h2>
      {description ? (
        <p
          className={`mt-5 text-pretty text-base leading-7 sm:text-lg ${
            inverse ? "text-white/65" : "text-slate"
          }`}
        >
          {description}
        </p>
      ) : null}
    </div>
  );
}
