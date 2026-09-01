"use client";

import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useRef, useState } from "react";
import { ArrowLeft, ImagePlus, LoaderCircle, Plus, Save, Trash2, X } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import type { RequestAsset, WebsiteRequest } from "@/lib/customer-lifecycle";
import { websitePlans } from "@/lib/plans";
import { acceptedPhotoTypes, MAX_PHOTOS, MAX_PHOTO_SIZE, WEBSITE_REQUEST_PHOTO_BUCKET, websiteRequestSchema } from "@/lib/website-request";

const fieldClass = "mt-2 w-full border border-white/14 bg-white/[0.045] px-4 py-3.5 text-[15px] text-white outline-none transition placeholder:text-white/24 focus:border-[#c9ff3b]/70";
const extensions: Record<string, string> = { "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/avif": "avif" };

export function RequestEditor({ request }: { request: WebsiteRequest }) {
  const supabase = useMemo(() => createClient(), []);
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);
  const [plan, setPlan] = useState(request.plan_id);
  const [offerings, setOfferings] = useState((request.website_request_offerings ?? []).map((item) => ({ ...item, price: String(item.price) })));
  const [assets, setAssets] = useState<RequestAsset[]>(request.website_request_assets ?? []);
  const [newPhotos, setNewPhotos] = useState<File[]>([]);
  const [photoBrief, setPhotoBrief] = useState(request.photo_brief ?? "");
  const [themeDescription, setThemeDescription] = useState(request.theme_description ?? "");
  const [additionalNotes, setAdditionalNotes] = useState(request.additional_notes ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateOffering(index: number, field: "title" | "description" | "price", value: string) {
    setOfferings((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item));
  }
  function choosePhotos(files: File[]) {
    const combined = [...newPhotos, ...files];
    if (assets.length + combined.length > MAX_PHOTOS) return setError(`A request can have up to ${MAX_PHOTOS} photos.`);
    if (combined.some((file) => !acceptedPhotoTypes.includes(file.type as never) || file.size > MAX_PHOTO_SIZE)) return setError("Photos must be JPG, PNG, WebP, or AVIF and no larger than 8 MB each.");
    setError(null); setNewPhotos(combined);
  }
  async function removeExisting(asset: RequestAsset) {
    setBusy(true); setError(null);
    const { error: databaseError } = await supabase.rpc("remove_request_asset", { p_asset_id: asset.id });
    if (databaseError) { setError(databaseError.message); setBusy(false); return; }
    await supabase.storage.from(WEBSITE_REQUEST_PHOTO_BUCKET).remove([asset.storage_path]);
    setAssets((current) => current.filter((item) => item.id !== asset.id));
    setBusy(false);
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(null);
    const parsed = websiteRequestSchema.safeParse({ plan, offerings, photoBrief, themeDescription, additionalNotes });
    if (!parsed.success) { setError("Review the plan and each offering before saving."); setBusy(false); return; }
    const { error: updateError } = await supabase.rpc("update_website_request", { p_request_id: request.id, p_plan_id: parsed.data.plan, p_offerings: parsed.data.offerings, p_photo_brief: parsed.data.photoBrief || null, p_theme_description: parsed.data.themeDescription || null, p_additional_notes: parsed.data.additionalNotes || null });
    if (updateError) { setError(updateError.message); setBusy(false); return; }
    if (newPhotos.length) {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) { setError("Your session expired. Sign in again."); setBusy(false); return; }
      const group = crypto.randomUUID();
      const uploaded: string[] = [];
      const metadata = [];
      try {
        for (const [index, file] of newPhotos.entries()) {
          const path = `${user.id}/${group}/${String(index + 1).padStart(2, "0")}.${extensions[file.type]}`;
          const { error: uploadError } = await supabase.storage.from(WEBSITE_REQUEST_PHOTO_BUCKET).upload(path, file, { cacheControl: "3600", contentType: file.type, upsert: false });
          if (uploadError) throw uploadError;
          uploaded.push(path);
          metadata.push({ storage_path: path, original_filename: file.name.slice(0, 255), mime_type: file.type, size_bytes: file.size });
        }
        const { error: assetError } = await supabase.rpc("add_request_assets", { p_request_id: request.id, p_assets: metadata });
        if (assetError) throw assetError;
      } catch (uploadError) {
        if (uploaded.length) await supabase.storage.from(WEBSITE_REQUEST_PHOTO_BUCKET).remove(uploaded);
        setError(uploadError instanceof Error ? uploadError.message : "Could not save the new photos."); setBusy(false); return;
      }
    }
    router.push(`/portal/requests/${request.id}`); router.refresh();
  }

  return <form onSubmit={save} className="space-y-8">
    {error ? <div role="alert" className="flex gap-3 border border-[#ff8f7e]/30 bg-[#ff725e]/8 px-4 py-3 text-sm text-[#ffb4a8]"><X className="size-4 shrink-0" />{error}</div> : null}
    <section className="border border-white/12 bg-white/[0.025] p-6 sm:p-8"><h2 className="text-3xl font-semibold tracking-[-0.05em]">Plan</h2><div className="mt-6 grid gap-3 sm:grid-cols-2">{websitePlans.map((item) => <button type="button" key={item.id} onClick={() => setPlan(item.id)} className={`border p-5 text-left ${plan === item.id ? "border-[#c9ff3b] bg-[#c9ff3b]/7" : "border-white/14"}`}><span className="block text-xl font-semibold">{item.name}</span><span className="mt-2 block text-sm text-white/42">{item.price}</span></button>)}</div></section>
    <section className="border border-white/12 bg-white/[0.025] p-6 sm:p-8"><div className="flex items-center justify-between"><h2 className="text-3xl font-semibold tracking-[-0.05em]">Offerings</h2><button type="button" className="button-secondary !px-3 !py-2" onClick={() => offerings.length < 20 && setOfferings((current) => [...current, { id: -Date.now(), title: "", description: "", price: "", position: current.length }])}><Plus className="size-4" />Add</button></div><div className="mt-6 space-y-4">{offerings.map((offering, index) => <fieldset key={offering.id} className="relative border border-white/10 p-5"><legend className="px-2 text-[10px] uppercase tracking-[0.14em] text-white/30">Offering {index + 1}</legend>{offerings.length > 1 ? <button type="button" onClick={() => setOfferings((current) => current.filter((_, i) => i !== index))} className="absolute right-3 top-3 text-white/28 hover:text-[#ff8f7e]" aria-label={`Remove ${offering.title || `offering ${index + 1}`}`}><Trash2 className="size-4" /></button> : null}<div className="grid gap-4 sm:grid-cols-[1fr_10rem]"><label className="text-xs font-semibold text-white/58">Title<input className={fieldClass} value={offering.title} onChange={(e) => updateOffering(index, "title", e.target.value)} maxLength={100} required /></label><label className="text-xs font-semibold text-white/58">Price<input className={fieldClass} value={String(offering.price)} onChange={(e) => updateOffering(index, "price", e.target.value)} inputMode="decimal" required /></label></div><label className="mt-4 block text-xs font-semibold text-white/58">Description<textarea className={`${fieldClass} min-h-28 resize-y`} value={offering.description} onChange={(e) => updateOffering(index, "description", e.target.value)} maxLength={1000} required /></label></fieldset>)}</div></section>
    <section className="border border-white/12 bg-white/[0.025] p-6 sm:p-8"><h2 className="text-3xl font-semibold tracking-[-0.05em]">Photos</h2><div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3">{assets.map((asset) => <div key={asset.id} className="relative">{asset.signedUrl ? <Image unoptimized src={asset.signedUrl} alt={asset.original_filename} width={600} height={600} className="aspect-square w-full object-cover" /> : <div className="grid aspect-square place-items-center bg-white/5"><ImagePlus className="size-6 text-white/24" /></div>}<button type="button" disabled={busy} onClick={() => removeExisting(asset)} className="absolute right-2 top-2 grid size-8 place-items-center bg-black/80 text-white hover:text-[#ff8f7e]" aria-label={`Remove ${asset.original_filename}`}><Trash2 className="size-4" /></button></div>)}{newPhotos.map((file, index) => <div key={`${file.name}-${index}`} className="relative grid aspect-square place-items-center border border-[#c9ff3b]/30 bg-[#c9ff3b]/5 p-3 text-center text-xs text-white/58"><ImagePlus className="size-6" /><span className="line-clamp-2">{file.name}</span><button type="button" onClick={() => setNewPhotos((current) => current.filter((_, i) => i !== index))} className="absolute right-2 top-2 text-white/38 hover:text-white"><X className="size-4" /></button></div>)}</div><input ref={fileInput} className="sr-only" type="file" accept={acceptedPhotoTypes.join(",")} multiple onChange={(e) => { if (e.target.files) choosePhotos(Array.from(e.target.files)); e.target.value = ""; }} /><button type="button" className="button-secondary mt-5" onClick={() => fileInput.current?.click()} disabled={assets.length + newPhotos.length >= MAX_PHOTOS}><ImagePlus className="size-4" />Add photos</button><label className="mt-6 block text-xs font-semibold text-white/58">Image direction<textarea className={`${fieldClass} min-h-32 resize-y`} value={photoBrief} onChange={(e) => setPhotoBrief(e.target.value)} maxLength={3000} /></label></section>
    <section className="border border-white/12 bg-white/[0.025] p-6 sm:p-8"><h2 className="text-3xl font-semibold tracking-[-0.05em]">Creative direction</h2><label className="mt-6 block text-xs font-semibold text-white/58">Theme<textarea className={`${fieldClass} min-h-40 resize-y`} value={themeDescription} onChange={(e) => setThemeDescription(e.target.value)} maxLength={3000} /></label><label className="mt-6 block text-xs font-semibold text-white/58">Additional notes<textarea className={`${fieldClass} min-h-40 resize-y`} value={additionalNotes} onChange={(e) => setAdditionalNotes(e.target.value)} maxLength={5000} /></label></section>
    <div className="flex flex-col-reverse gap-3 border-t border-white/10 pt-6 sm:flex-row sm:justify-between"><Link href={`/portal/requests/${request.id}`} className="button-secondary justify-center"><ArrowLeft className="size-4" />Cancel</Link><button type="submit" className="button-primary justify-center" disabled={busy}>{busy ? <LoaderCircle className="size-4 animate-spin" /> : <Save className="size-4" />}{busy ? "Saving…" : "Save request"}</button></div>
  </form>;
}
