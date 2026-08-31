import { z } from "zod";

export const MAX_PHOTOS = 8;
export const MAX_PHOTO_SIZE = 8 * 1024 * 1024;
export const WEBSITE_REQUEST_PHOTO_BUCKET = "website-request-photos";

export const acceptedPhotoTypes = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/avif",
] as const;

export const offeringSchema = z.object({
  title: z.string().trim().min(2, "Add a title.").max(100),
  description: z.string().trim().min(2, "Add a description.").max(1000),
  price: z
    .string()
    .trim()
    .regex(/^\d{1,10}(?:\.\d{1,2})?$/, "Use a valid price, such as 25 or 25.00.")
    .refine((value) => Number(value) <= 9_999_999_999.99, "That price is too large."),
});

export const websiteRequestSchema = z.object({
  plan: z.enum(["starter", "pro"]),
  offerings: z.array(offeringSchema).min(1).max(20),
  photoBrief: z.string().trim().max(3000),
  themeDescription: z.string().trim().max(3000),
  additionalNotes: z.string().trim().max(5000),
});

export type WebsiteRequestPayload = z.infer<typeof websiteRequestSchema>;
