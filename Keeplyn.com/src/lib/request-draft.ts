"use client";

/**
 * The /start answers (photos included) kept in this browser's IndexedDB, so a
 * refresh doesn't lose them and the request can be sent automatically once the
 * visitor confirms their email. Every call fails quietly: private windows and
 * blocked storage just mean no draft.
 */
export type RequestDraft = {
  plan: "starter" | "pro" | null;
  businessName: string;
  offerings: { title: string; description: string; price: string }[];
  photos: File[];
  photoBrief: string;
  themeTags: string[];
  themeDescription: string;
  additionalNotes: string;
  fullName: string;
  email: string;
  /** Set once the account was created and we're waiting for the email link. */
  awaitingConfirmation: boolean;
  savedAt: number;
};

const DB_NAME = "keeplyn";
const STORE = "drafts";
const KEY = "website-request";
// Photos live under their own key so typing doesn't re-copy megabytes of images.
const PHOTOS_KEY = "website-request-photos";
const MAX_AGE = 14 * 24 * 60 * 60 * 1000;

function openDb() {
  return new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function withStore<T>(mode: IDBTransactionMode, run: (store: IDBObjectStore) => IDBRequest<T>) {
  const db = await openDb();
  try {
    return await new Promise<T>((resolve, reject) => {
      const request = run(db.transaction(STORE, mode).objectStore(STORE));
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  } finally {
    db.close();
  }
}

export async function loadDraft(): Promise<RequestDraft | null> {
  try {
    const draft = await withStore<Omit<RequestDraft, "photos"> | undefined>("readonly", (store) => store.get(KEY));
    if (!draft || Date.now() - draft.savedAt > MAX_AGE) return null;
    const photos = await withStore<File[] | undefined>("readonly", (store) => store.get(PHOTOS_KEY));
    return { ...draft, photos: photos ?? [] };
  } catch {
    return null;
  }
}

export async function saveDraft(draft: Omit<RequestDraft, "savedAt" | "photos">) {
  try {
    await withStore("readwrite", (store) => store.put({ ...draft, savedAt: Date.now() }, KEY));
  } catch {
    // No storage available; the form still works, it just won't survive a reload.
  }
}

export async function savePhotos(photos: File[]) {
  try {
    await withStore("readwrite", (store) => store.put(photos, PHOTOS_KEY));
  } catch {
    // Same as above: the photos stay in memory for this visit.
  }
}

export async function clearDraft() {
  try {
    await withStore("readwrite", (store) => store.delete(KEY));
    await withStore("readwrite", (store) => store.delete(PHOTOS_KEY));
  } catch {
    // Nothing to clear.
  }
}

/** Accepts "1,200", "$40", "40.5"; anything else ("50/hr", "from 40") goes into the description. */
export function normalizeOffering(offering: { title: string; description: string; price: string }) {
  const raw = offering.price.trim();
  const cleaned = raw.replace(/^\$\s*/, "").replace(/,/g, "");
  if (!raw || /^\d{1,10}(?:\.\d{1,2})?$/.test(cleaned)) return { ...offering, price: cleaned };
  const description = `${offering.description.trim()}\n\nPrice: ${raw}`.slice(0, 1000);
  return { ...offering, description, price: "" };
}
