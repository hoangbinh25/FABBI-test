import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Tag } from "../api/tags";
import { useUpdateTag } from "../api/tags";
import { tagSchema, type TagFormData } from "../schemas/tag";

interface TagEditDialogProps {
  tag: Tag | null;
  onClose: () => void;
}

export function TagEditDialog({ tag, onClose }: TagEditDialogProps) {
  const updateTag = useUpdateTag();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TagFormData>({
    resolver: zodResolver(tagSchema),
  });

  useEffect(() => {
    reset({ name: tag?.name ?? "", color: tag?.color ?? "" });
  }, [tag, reset]);

  const submit = (data: TagFormData) => {
    if (!tag) return;
    updateTag.mutate(
      { id: tag.id, name: data.name, color: data.color || undefined },
      { onSuccess: onClose },
    );
  };

  return (
    <Dialog open={tag !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit tag</DialogTitle>
        </DialogHeader>
        <form className="space-y-4" onSubmit={handleSubmit(submit)}>
          <div className="space-y-2">
            <Label htmlFor="tag-name">Name</Label>
            <Input id="tag-name" {...register("name")} />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="tag-color">Color (optional)</Label>
            <Input id="tag-color" placeholder="#dbeafe" {...register("color")} />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={updateTag.isPending}>
              Save
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
