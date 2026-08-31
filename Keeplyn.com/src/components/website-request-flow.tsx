"use client";

import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronLeft,
  ImagePlus,
  LoaderCircle,
  LockKeyhole,
  Plus,
  Sparkles,
  Trash2,
  UploadCloud,
  X,
} from "lucide-react";
import { FormEvent, useMemo, useRef, useState } from "react";
import { BrandLogo } from "@/components/brand-logo";
import { createClient } from "@/lib/supabase/client";
import { websitePlans, type WebsitePlan } from "@/lib/plans";
import {
  acceptedPhotoTypes,
  MAX_PHOTOS,
  MAX_PHOTO_SIZE,
  WEBSITE_REQUEST_PHOTO_BUCKET,
  websiteRequestSchema,
} from "@/lib/website-request";

type PlanId = WebsitePlan["id"];

type InitialUser = {
  id: string;
  email: string;
  name: string;
};

type Offering = {
  title: string;
  description: string;
  price: string;
};

type WebsiteRequestFlowProps = {
  initialUser: InitialUser | null;
  initialPlan: PlanId | null;
};

const flowSteps = [
  { label: "Account", eyebrow: "Create your login" },
  { label: "Plan", eyebrow: "Choose your build" },
  { label: "Offerings", eyebrow: "What you sell" },
  { label: "Photos", eyebrow: "Show the work" },
  { label: "Theme", eyebrow: "Set the feeling" },
  { label: "Final notes", eyebrow: "Anything else" },
] as const;

const themeOptions = [
  "Clean & minimal",
  "Warm & editorial",
  "Bold & energetic",
  "Playful & friendly",
  "Polished & premium",
  "Modern & technical",
] as const;

const fieldClass =
  "mt-2 w-full border border-white/14 bg-white/[0.045] px-4 py-3.5 text-[15px] text-white outline-none transition placeholder:text-white/24 focus:border-[#c9ff3b]/70 focus:bg-white/[0.07]";

const emptyOffering = (): Offering => ({ title: "", description: "", price: "" });

const mimeExtensions: Record<string, string> = {
  "image/jpeg": "jpg",
  "image/png": "png",
  "image/webp": "webp",
  "image/avif": "avif",
};

function formatBytes(bytes: number) {
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function StepHeading({
  kicker,
  title,
  description,
}: {
  kicker: string;
  title: string;
  description: string;
}) {
  return (
    <div className="mb-10">
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#c9ff3b]">
        {kicker}
      </p>
      <h1 className="mt-4 max-w-3xl text-[clamp(3rem,7vw,6.5rem)] font-semibold leading-[0.82] tracking-[-0.075em]">
        {title}
      </h1>
      <p className="mt-6 max-w-2xl text-sm leading-7 text-white/48 sm:text-base">
        {description}
      </p>
    </div>
  );
}

export function WebsiteRequestFlow({
  initialUser,
  initialPlan,
}: WebsiteRequestFlowProps) {
  const supabase = useMemo(() => createClient(), []);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [step, setStep] = useState(initialUser ? 1 : 0);
  const [accountMode, setAccountMode] = useState<"signup" | "signin">("signup");
  const [currentUser, setCurrentUser] = useState(initialUser);
  const [fullName, setFullName] = useState(initialUser?.name ?? "");
  const [email, setEmail] = useState(initialUser?.email ?? "");
  const [password, setPassword] = useState("");
  const [plan, setPlan] = useState<PlanId | null>(initialPlan);
  const [offerings, setOfferings] = useState<Offering[]>([emptyOffering()]);
  const [photos, setPhotos] = useState<File[]>([]);
  const [photoBrief, setPhotoBrief] = useState("");
  const [themeTags, setThemeTags] = useState<string[]>([]);
  const [themeDescription, setThemeDescription] = useState("");
  const [additionalNotes, setAdditionalNotes] = useState("");
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [requestId, setRequestId] = useState<number | null>(null);

  const selectedPlan = websitePlans.find((item) => item.id === plan) ?? null;
  const minimumStep = currentUser ? 1 : 0;

  async function handleAccountSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (fullName.trim().length < 2 && accountMode === "signup") {
      setError("Please add your name.");
      return;
    }

    if (!email.trim() || password.length < 8) {
      setError("Use a valid email and a password with at least 8 characters.");
      return;
    }

    setBusy(true);

    if (accountMode === "signup") {
      const { data, error: signUpError } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          data: { full_name: fullName.trim() },
        },
      });

      setBusy(false);

      if (signUpError) {
        setError(signUpError.message);
        return;
      }

      if (!data.session || !data.user) {
        setError("We couldn't finish creating your account. Please try again.");
        return;
      }

      setCurrentUser({
        id: data.user.id,
        email: data.user.email ?? email.trim(),
        name: fullName.trim(),
      });
      setStep(1);
      return;
    }

    const { data, error: signInError } = await supabase.auth.signInWithPassword({
      email: email.trim(),
      password,
    });

    setBusy(false);

    if (signInError) {
      setError("We couldn't sign you in with that email and password.");
      return;
    }

    setCurrentUser({
      id: data.user.id,
      email: data.user.email ?? email.trim(),
      name:
        typeof data.user.user_metadata.full_name === "string"
          ? data.user.user_metadata.full_name
          : "",
    });
    setStep(1);
  }

  function goNext() {
    setError(null);

    if (step === 1 && !plan) {
      setError("Choose a plan to continue.");
      return;
    }

    if (step === 2) {
      const result = websiteRequestSchema.shape.offerings.safeParse(offerings);
      if (!result.success) {
        setError("Give every offering a title, description, and valid price.");
        return;
      }
    }

    setStep((current) => Math.min(current + 1, flowSteps.length - 1));
  }

  function goBack() {
    setError(null);
    setStep((current) => Math.max(current - 1, minimumStep));
  }

  function updateOffering(index: number, field: keyof Offering, value: string) {
    setOfferings((current) =>
      current.map((offering, offeringIndex) =>
        offeringIndex === index ? { ...offering, [field]: value } : offering,
      ),
    );
  }

  function addOffering() {
    if (offerings.length < 20) {
      setOfferings((current) => [...current, emptyOffering()]);
    }
  }

  function removeOffering(index: number) {
    if (offerings.length > 1) {
      setOfferings((current) => current.filter((_, offeringIndex) => offeringIndex !== index));
    }
  }

  function choosePhotos(files: File[]) {
    setError(null);
    const acceptedTypes = new Set<string>(acceptedPhotoTypes);
    const combined = [...photos, ...files];

    if (combined.length > MAX_PHOTOS) {
      setError(`Choose no more than ${MAX_PHOTOS} photos.`);
      return;
    }

    const invalidFile = combined.find(
      (file) => !acceptedTypes.has(file.type) || file.size > MAX_PHOTO_SIZE,
    );

    if (invalidFile) {
      setError("Photos must be JPG, PNG, WebP, or AVIF files no larger than 8 MB each.");
      return;
    }

    setPhotos(combined);
  }

  function toggleTheme(theme: string) {
    setThemeTags((current) =>
      current.includes(theme)
        ? current.filter((item) => item !== theme)
        : [...current, theme],
    );
  }

  async function submitRequest() {
    setError(null);

    const combinedTheme = [
      themeTags.length ? `Preferred directions: ${themeTags.join(", ")}.` : "",
      themeDescription.trim(),
    ]
      .filter(Boolean)
      .join("\n\n");

    const parsed = websiteRequestSchema.safeParse({
      plan,
      offerings,
      photoBrief,
      themeDescription: combinedTheme,
      additionalNotes,
    });

    if (!parsed.success) {
      setError("Please review the required plan and offering details before submitting.");
      return;
    }

    setBusy(true);
    const uploadedPaths: string[] = [];

    try {
      const {
        data: { user },
        error: userError,
      } = await supabase.auth.getUser();

      if (userError || !user) {
        throw new Error("Your session has expired. Please sign in again.");
      }

      const uploadGroup = crypto.randomUUID();
      const assets: Array<{
        storage_path: string;
        original_filename: string;
        mime_type: string;
        size_bytes: number;
      }> = [];

      for (const [index, file] of photos.entries()) {
        const extension = mimeExtensions[file.type];
        const path = `${user.id}/${uploadGroup}/${String(index + 1).padStart(2, "0")}.${extension}`;
        const { error: uploadError } = await supabase.storage
          .from(WEBSITE_REQUEST_PHOTO_BUCKET)
          .upload(path, file, {
            cacheControl: "3600",
            contentType: file.type,
            upsert: false,
          });

        if (uploadError) throw uploadError;

        uploadedPaths.push(path);
        assets.push({
          storage_path: path,
          original_filename: file.name.slice(0, 255),
          mime_type: file.type,
          size_bytes: file.size,
        });
      }

      const { data, error: requestError } = await supabase.rpc("submit_website_request", {
        p_plan_id: parsed.data.plan,
        p_offerings: parsed.data.offerings,
        p_photo_brief: parsed.data.photoBrief || null,
        p_theme_description: parsed.data.themeDescription || null,
        p_additional_notes: parsed.data.additionalNotes || null,
        p_assets: assets,
      });

      if (requestError) throw requestError;

      setRequestId(Number(data));
    } catch (submissionError) {
      if (uploadedPaths.length) {
        await supabase.storage.from(WEBSITE_REQUEST_PHOTO_BUCKET).remove(uploadedPaths);
      }

      setError(
        submissionError instanceof Error && submissionError.message.includes("session")
          ? submissionError.message
          : "We couldn't send your request. Please try again, or email hello@keeplyn.com.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (requestId !== null) {
    return (
      <main className="relative min-h-svh overflow-hidden bg-[#050505] text-white">
        <div className="pointer-events-none absolute left-1/2 top-1/2 size-[48rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#7568ff]/12 blur-[180px]" />
        <div className="site-container relative flex min-h-svh flex-col py-6 sm:py-8">
          <BrandLogo inverse />
          <div className="my-auto max-w-5xl py-20">
            <CheckCircle2 className="size-12 text-[#c9ff3b]" strokeWidth={1.5} aria-hidden="true" />
            <p className="mt-8 text-[10px] font-semibold uppercase tracking-[0.2em] text-[#c9ff3b]">
              Request #{String(requestId).padStart(4, "0")}
            </p>
            <h1 className="mt-5 text-[clamp(4.5rem,13vw,11rem)] font-semibold leading-[0.74] tracking-[-0.09em]">
              We&apos;ve got it.
            </h1>
            <p className="mt-9 max-w-xl text-base leading-7 text-white/52">
              Your brief is safely in our hands. Keeplyn will review everything and send your custom demo within two business days.
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <Link href="/" className="button-primary">
                Back to Keeplyn
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
              <a href="mailto:hello@keeplyn.com" className="button-secondary">
                Ask a question
              </a>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-svh bg-[#050505] text-white">
      <header className="border-b border-white/10 bg-black/70 backdrop-blur-xl">
        <div className="site-container flex h-[68px] items-center justify-between">
          <BrandLogo inverse />
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.1em] text-white/42 transition-colors hover:text-white"
          >
            <ArrowLeft className="size-3.5" aria-hidden="true" />
            Exit
          </Link>
        </div>
      </header>

      <div className="site-container grid min-h-[calc(100svh-68px)] gap-10 py-8 lg:grid-cols-[16rem_minmax(0,1fr)_15rem] lg:gap-12 lg:py-12 xl:gap-16">
        <aside className="lg:sticky lg:top-10 lg:h-fit" aria-label="Request progress">
          <div className="mb-8 flex items-center justify-between lg:hidden">
            <p className="text-xs font-semibold text-white/68">
              {flowSteps[step].label}
            </p>
            <p className="text-xs text-white/34">
              {step + 1} / {flowSteps.length}
            </p>
          </div>
          <div className="mb-10 h-1 overflow-hidden bg-white/10 lg:hidden">
            <div
              className="h-full bg-[#c9ff3b] transition-[width] duration-500"
              style={{ width: `${((step + 1) / flowSteps.length) * 100}%` }}
            />
          </div>

          <ol className="hidden space-y-1 lg:block">
            {flowSteps.map((item, index) => {
              const complete = index < step;
              const active = index === step;

              return (
                <li
                  key={item.label}
                  className={`grid grid-cols-[2rem_1fr] gap-3 border-l px-4 py-3 transition-colors ${
                    active
                      ? "border-[#c9ff3b] bg-white/[0.045]"
                      : "border-white/10"
                  }`}
                  aria-current={active ? "step" : undefined}
                >
                  <span
                    className={`grid size-7 place-items-center rounded-full border text-[10px] font-semibold ${
                      complete
                        ? "border-[#c9ff3b] bg-[#c9ff3b] text-black"
                        : active
                          ? "border-[#c9ff3b]/55 text-[#c9ff3b]"
                          : "border-white/14 text-white/30"
                    }`}
                  >
                    {complete ? <Check className="size-3.5" aria-hidden="true" /> : index + 1}
                  </span>
                  <span>
                    <span className={`block text-sm font-semibold ${active ? "text-white" : "text-white/42"}`}>
                      {item.label}
                    </span>
                    <span className="mt-0.5 block text-[10px] text-white/24">{item.eyebrow}</span>
                  </span>
                </li>
              );
            })}
          </ol>
        </aside>

        <section className="min-w-0 pb-12 lg:pb-20">
          {error ? (
            <div className="mb-7 flex items-start gap-3 border border-[#ff8f7e]/30 bg-[#ff725e]/8 px-4 py-3 text-sm text-[#ffb4a8]" role="alert">
              <X className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
              {error}
            </div>
          ) : null}

          {step === 0 ? (
            <>
              <StepHeading
                kicker="Step 01 / Account"
                title={accountMode === "signup" ? "First, let’s know you." : "Welcome back."}
                description={
                  accountMode === "signup"
                    ? "Create a secure account so your request, photos, and future website updates stay connected to you."
                    : "Sign in to continue a new website request with your account."
                }
              />
              <form onSubmit={handleAccountSubmit} className="max-w-2xl space-y-6">
                {accountMode === "signup" ? (
                  <label className="block text-xs font-semibold text-white/62">
                    Your name
                    <input
                      className={fieldClass}
                      autoComplete="name"
                      value={fullName}
                      onChange={(event) => setFullName(event.target.value)}
                      placeholder="Alex Morgan"
                      maxLength={100}
                      required
                    />
                  </label>
                ) : null}
                <label className="block text-xs font-semibold text-white/62">
                  Email address
                  <input
                    className={fieldClass}
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@business.com"
                    required
                  />
                </label>
                <label className="block text-xs font-semibold text-white/62">
                  Password
                  <input
                    className={fieldClass}
                    type="password"
                    autoComplete={accountMode === "signup" ? "new-password" : "current-password"}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="At least 8 characters"
                    minLength={8}
                    required
                  />
                </label>
                <div className="flex flex-col gap-4 pt-2 sm:flex-row sm:items-center sm:justify-between">
                  <button type="submit" className="button-primary justify-center" disabled={busy}>
                    {busy ? <LoaderCircle className="size-4 animate-spin" aria-hidden="true" /> : null}
                    {accountMode === "signup" ? "Create account" : "Sign in"}
                    {!busy ? <ArrowRight className="size-4" aria-hidden="true" /> : null}
                  </button>
                  <button
                    type="button"
                    className="text-sm text-white/42 underline decoration-white/18 underline-offset-4 transition hover:text-white"
                    onClick={() => {
                      setError(null);
                      setAccountMode((mode) => (mode === "signup" ? "signin" : "signup"));
                    }}
                  >
                    {accountMode === "signup" ? "Already have an account? Sign in" : "Need an account? Sign up"}
                  </button>
                </div>
              </form>
            </>
          ) : null}

          {step === 1 ? (
            <>
              <StepHeading
                kicker="Step 02 / Plan"
                title="Choose your build."
                description="Pick the foundation that fits your business today. You can review everything before submitting—no payment is taken here."
              />
              <div className="grid gap-4 md:grid-cols-2">
                {websitePlans.map((item) => {
                  const active = plan === item.id;
                  return (
                    <button
                      type="button"
                      key={item.id}
                      aria-pressed={active}
                      onClick={() => setPlan(item.id)}
                      className={`relative min-h-80 border p-6 text-left transition sm:p-8 ${
                        active
                          ? "border-[#c9ff3b] bg-[#c9ff3b]/[0.065]"
                          : "border-white/14 bg-white/[0.025] hover:border-white/32 hover:bg-white/[0.045]"
                      }`}
                    >
                      <span className={`absolute right-5 top-5 grid size-7 place-items-center rounded-full border ${active ? "border-[#c9ff3b] bg-[#c9ff3b] text-black" : "border-white/20 text-transparent"}`}>
                        <Check className="size-4" aria-hidden="true" />
                      </span>
                      <span className="block text-4xl font-semibold tracking-[-0.065em]">{item.name}</span>
                      <span className="mt-5 block max-w-xs text-sm leading-6 text-white/44">{item.summary}</span>
                      <span className="mt-14 block text-5xl font-semibold tracking-[-0.075em]">{item.price}</span>
                      <span className="mt-3 block text-xs text-[#c9ff3b]">Optional {item.hosting} care plan</span>
                    </button>
                  );
                })}
              </div>
            </>
          ) : null}

          {step === 2 ? (
            <>
              <StepHeading
                kicker="Step 03 / Offerings"
                title="What do you offer?"
                description="Add the products, services, packages, or menu items you want customers to see. Use the price you want displayed."
              />
              <div className="space-y-5">
                {offerings.map((offering, index) => (
                  <fieldset key={index} className="relative border border-white/14 bg-white/[0.025] p-5 sm:p-7">
                    <legend className="px-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/34">
                      Offering {String(index + 1).padStart(2, "0")}
                    </legend>
                    {offerings.length > 1 ? (
                      <button
                        type="button"
                        className="absolute right-4 top-4 grid size-9 place-items-center border border-white/12 text-white/34 transition hover:border-[#ff8f7e]/50 hover:text-[#ff8f7e]"
                        onClick={() => removeOffering(index)}
                        aria-label={`Remove offering ${index + 1}`}
                      >
                        <Trash2 className="size-4" aria-hidden="true" />
                      </button>
                    ) : null}
                    <div className="grid gap-5 sm:grid-cols-[minmax(0,1fr)_11rem]">
                      <label className="block text-xs font-semibold text-white/62">
                        Title
                        <input
                          className={fieldClass}
                          value={offering.title}
                          onChange={(event) => updateOffering(index, "title", event.target.value)}
                          placeholder="Signature consultation"
                          maxLength={100}
                        />
                      </label>
                      <label className="block text-xs font-semibold text-white/62">
                        Price
                        <span className="relative block">
                          <span className="pointer-events-none absolute left-4 top-[1.4rem] -translate-y-1/2 text-sm text-white/34">$</span>
                          <input
                            className={`${fieldClass} pl-8`}
                            inputMode="decimal"
                            value={offering.price}
                            onChange={(event) => updateOffering(index, "price", event.target.value)}
                            placeholder="125.00"
                            aria-label={`Offering ${index + 1} price in dollars`}
                          />
                        </span>
                      </label>
                    </div>
                    <label className="mt-5 block text-xs font-semibold text-white/62">
                      Description
                      <textarea
                        className={`${fieldClass} min-h-28 resize-y`}
                        value={offering.description}
                        onChange={(event) => updateOffering(index, "description", event.target.value)}
                        placeholder="What is included, who it is for, and why customers choose it."
                        maxLength={1000}
                      />
                    </label>
                  </fieldset>
                ))}
                <button
                  type="button"
                  className="flex w-full items-center justify-center gap-2 border border-dashed border-white/18 px-5 py-5 text-sm font-semibold text-white/48 transition hover:border-[#c9ff3b]/60 hover:text-[#c9ff3b] disabled:cursor-not-allowed disabled:opacity-40"
                  onClick={addOffering}
                  disabled={offerings.length >= 20}
                >
                  <Plus className="size-4" aria-hidden="true" />
                  Add another offering
                </button>
              </div>
            </>
          ) : null}

          {step === 3 ? (
            <>
              <StepHeading
                kicker="Step 04 / Photos"
                title="Show us—or describe it."
                description="Upload photos you already love, describe images you want us to generate, or skip this step and let us guide the art direction."
              />
              <div
                className={`border border-dashed p-8 text-center transition sm:p-12 ${dragging ? "border-[#c9ff3b] bg-[#c9ff3b]/7" : "border-white/20 bg-white/[0.02]"}`}
                onDragEnter={(event) => {
                  event.preventDefault();
                  setDragging(true);
                }}
                onDragOver={(event) => event.preventDefault()}
                onDragLeave={() => setDragging(false)}
                onDrop={(event) => {
                  event.preventDefault();
                  setDragging(false);
                  choosePhotos(Array.from(event.dataTransfer.files));
                }}
              >
                <UploadCloud className="mx-auto size-10 text-white/34" strokeWidth={1.5} aria-hidden="true" />
                <p className="mt-5 text-base font-semibold">Drop your photos here</p>
                <p className="mt-2 text-xs leading-5 text-white/34">JPG, PNG, WebP, or AVIF · up to 8 MB each · {MAX_PHOTOS} photos max</p>
                <input
                  ref={fileInputRef}
                  className="sr-only"
                  type="file"
                  accept={acceptedPhotoTypes.join(",")}
                  multiple
                  onChange={(event) => {
                    if (event.target.files) choosePhotos(Array.from(event.target.files));
                    event.target.value = "";
                  }}
                />
                <button type="button" className="button-secondary mt-6" onClick={() => fileInputRef.current?.click()}>
                  <ImagePlus className="size-4" aria-hidden="true" />
                  Choose photos
                </button>
              </div>

              {photos.length ? (
                <ul className="mt-4 divide-y divide-white/10 border border-white/12">
                  {photos.map((file, index) => (
                    <li key={`${file.name}-${file.lastModified}-${index}`} className="flex items-center gap-4 px-4 py-3">
                      <span className="grid size-9 shrink-0 place-items-center bg-white/[0.06] text-white/42">
                        <ImagePlus className="size-4" aria-hidden="true" />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-medium text-white/74">{file.name}</span>
                        <span className="mt-0.5 block text-[10px] text-white/30">{formatBytes(file.size)}</span>
                      </span>
                      <button
                        type="button"
                        className="grid size-9 place-items-center text-white/30 transition hover:text-[#ff8f7e]"
                        onClick={() => setPhotos((current) => current.filter((_, photoIndex) => photoIndex !== index))}
                        aria-label={`Remove ${file.name}`}
                      >
                        <X className="size-4" aria-hidden="true" />
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}

              <label className="mt-8 block text-xs font-semibold text-white/62">
                Images you want us to create <span className="font-normal text-white/28">(optional)</span>
                <textarea
                  className={`${fieldClass} min-h-36 resize-y`}
                  value={photoBrief}
                  onChange={(event) => setPhotoBrief(event.target.value)}
                  placeholder="For example: warm natural-light photos of a neighborhood bakery, close-ups of sourdough texture, no people, earthy tones…"
                  maxLength={3000}
                />
              </label>
            </>
          ) : null}

          {step === 4 ? (
            <>
              <StepHeading
                kicker="Step 05 / Theme"
                title="How should it feel?"
                description="Describe the visual world you want. Brand colors, reference sites, words, eras, and moods are all useful—but this step is optional."
              />
              <div className="flex flex-wrap gap-2">
                {themeOptions.map((theme) => {
                  const active = themeTags.includes(theme);
                  return (
                    <button
                      type="button"
                      key={theme}
                      aria-pressed={active}
                      onClick={() => toggleTheme(theme)}
                      className={`border px-4 py-3 text-sm transition ${active ? "border-[#c9ff3b] bg-[#c9ff3b] text-black" : "border-white/14 bg-white/[0.03] text-white/54 hover:border-white/36 hover:text-white"}`}
                    >
                      {theme}
                    </button>
                  );
                })}
              </div>
              <label className="mt-8 block text-xs font-semibold text-white/62">
                Your creative direction <span className="font-normal text-white/28">(optional)</span>
                <textarea
                  className={`${fieldClass} min-h-48 resize-y`}
                  value={themeDescription}
                  onChange={(event) => setThemeDescription(event.target.value)}
                  placeholder="I want it to feel calm, confident, and handcrafted. Our colors are deep green and cream. I like generous spacing and editorial typography…"
                  maxLength={3000}
                />
              </label>
            </>
          ) : null}

          {step === 5 ? (
            <>
              <StepHeading
                kicker="Step 06 / Final notes"
                title="Anything else?"
                description="Share deadlines, must-have pages, links to an existing site, special functionality, or anything else we should know before we begin."
              />
              <label className="block text-xs font-semibold text-white/62">
                Final notes <span className="font-normal text-white/28">(optional)</span>
                <textarea
                  className={`${fieldClass} min-h-52 resize-y`}
                  value={additionalNotes}
                  onChange={(event) => setAdditionalNotes(event.target.value)}
                  placeholder="We are hoping to launch before our October opening. We need Home, About, Services, FAQ, and Contact pages…"
                  maxLength={5000}
                />
              </label>
              <div className="mt-8 border border-[#c9ff3b]/22 bg-[#c9ff3b]/[0.045] p-5 sm:p-6">
                <div className="flex items-start gap-4">
                  <Sparkles className="mt-0.5 size-5 shrink-0 text-[#c9ff3b]" aria-hidden="true" />
                  <div>
                    <p className="text-sm font-semibold">Ready for Keeplyn</p>
                    <p className="mt-2 text-sm leading-6 text-white/46">
                      We&apos;ll review your brief and create a custom website demo within two business days. You won&apos;t be charged until the website is exactly what you want.
                    </p>
                  </div>
                </div>
              </div>
            </>
          ) : null}

          {step >= 1 ? (
            <div className="mt-10 flex flex-col-reverse gap-3 border-t border-white/10 pt-6 sm:flex-row sm:items-center sm:justify-between">
              <button
                type="button"
                className="button-secondary justify-center disabled:cursor-not-allowed disabled:opacity-35"
                onClick={goBack}
                disabled={step <= minimumStep || busy}
              >
                <ChevronLeft className="size-4" aria-hidden="true" />
                Back
              </button>
              {step < flowSteps.length - 1 ? (
                <button type="button" className="button-primary justify-center" onClick={goNext}>
                  Continue
                  <ArrowRight className="size-4" aria-hidden="true" />
                </button>
              ) : (
                <button type="button" className="button-primary justify-center" onClick={submitRequest} disabled={busy}>
                  {busy ? <LoaderCircle className="size-4 animate-spin" aria-hidden="true" /> : <Sparkles className="size-4" aria-hidden="true" />}
                  {busy ? "Sending request…" : "Send website request"}
                </button>
              )}
            </div>
          ) : null}
        </section>

        <aside className="hidden lg:block">
          <div className="sticky top-10 border border-white/12 bg-white/[0.025] p-5">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">Your brief</p>
            <dl className="mt-6 space-y-5">
              <div>
                <dt className="text-[10px] uppercase tracking-[0.12em] text-white/26">Account</dt>
                <dd className="mt-1.5 truncate text-sm text-white/62">{currentUser?.email || email || "Not created"}</dd>
              </div>
              <div>
                <dt className="text-[10px] uppercase tracking-[0.12em] text-white/26">Plan</dt>
                <dd className="mt-1.5 text-sm text-white/62">{selectedPlan ? `${selectedPlan.name} · ${selectedPlan.price}` : "Not chosen"}</dd>
              </div>
              <div>
                <dt className="text-[10px] uppercase tracking-[0.12em] text-white/26">Offerings</dt>
                <dd className="mt-1.5 text-sm text-white/62">{offerings.filter((item) => item.title.trim()).length || "None yet"}</dd>
              </div>
              <div>
                <dt className="text-[10px] uppercase tracking-[0.12em] text-white/26">Photos</dt>
                <dd className="mt-1.5 text-sm text-white/62">{photos.length ? `${photos.length} selected` : "Optional"}</dd>
              </div>
            </dl>
            <div className="mt-7 flex gap-3 border-t border-white/10 pt-5 text-[10px] leading-5 text-white/30">
              <LockKeyhole className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
              Your request and photos are private and tied to your account.
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}
