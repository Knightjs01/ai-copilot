"use client";

import Image from "next/image";

import { Dropzone } from "@/components/ui/dropzone";
import { Field } from "@/components/ui/field";
import { API_URL } from "@/lib/api-client";

interface MediaStepProps {
  coverImageUrl: string | null;
  onUploadCoverImage: (file: File) => void;
  isUploadingCoverImage: boolean;
}

export function MediaStep({
  coverImageUrl,
  onUploadCoverImage,
  isUploadingCoverImage,
}: MediaStepProps) {
  return (
    <div className="flex flex-col gap-5">
      <Field label="Cover image">
        {coverImageUrl && (
          <div className="relative mb-3 h-32 w-full overflow-hidden rounded-2xl border border-border">
            <Image
              src={`${API_URL}${coverImageUrl}`}
              alt=""
              fill
              className="object-cover"
              unoptimized
            />
          </div>
        )}
        <Dropzone
          accept="image/png,image/jpeg,image/webp"
          label="Upload a cover image"
          hint="PNG, JPEG, or WebP, up to 5MB — shown at the top of your public profile"
          currentFileName={coverImageUrl ? "Cover image uploaded" : null}
          isUploading={isUploadingCoverImage}
          onFileSelected={onUploadCoverImage}
        />
      </Field>
    </div>
  );
}
