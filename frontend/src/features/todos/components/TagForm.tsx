import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreateTag } from "../api/tags";
import { tagSchema, type TagFormData } from "../schemas/tag";

export function TagForm() {
  const createTag = useCreateTag();
  const { register, handleSubmit, reset, formState: { errors } } = useForm<TagFormData>({ resolver: zodResolver(tagSchema) });
  return <form className="flex items-center gap-2" onSubmit={handleSubmit((data) => createTag.mutate(data, { onSuccess: () => reset() }))}>
    <div><Input className="max-w-48" placeholder="New tag" {...register("name")} />{errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}</div>
    <Button variant="outline" size="sm" type="submit" disabled={createTag.isPending}>Create tag</Button>
  </form>;
}
