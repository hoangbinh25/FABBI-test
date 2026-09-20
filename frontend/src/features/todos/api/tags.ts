import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";

export interface Tag {
  id: string;
  name: string;
  color: string | null;
}

interface TagInput {
  name: string;
  color?: string;
}

const refreshTagAndTodoQueries = () => {
  queryClient.invalidateQueries({ queryKey: ["tags"] });
  queryClient.invalidateQueries({ queryKey: ["todos"] });
};

export const useTags = () =>
  useQuery({
    queryKey: ["tags"],
    queryFn: async (): Promise<Tag[]> => (await api.get("/tags")).data,
  });

export const useCreateTag = () =>
  useMutation({
    mutationFn: (data: TagInput) => api.post("/tags", data),
    onSuccess: refreshTagAndTodoQueries,
  });

export const useDeleteTag = () =>
  useMutation({
    mutationFn: (id: string) => api.delete(`/tags/${id}`),
    onSuccess: refreshTagAndTodoQueries,
  });

export const useUpdateTag = () =>
  useMutation({
    mutationFn: ({ id, ...data }: TagInput & { id: string }) =>
      api.patch(`/tags/${id}`, data),
    onSuccess: refreshTagAndTodoQueries,
  });

export const useAttachTag = () =>
  useMutation({
    mutationFn: ({ todoId, tagId }: { todoId: string; tagId: string }) =>
      api.post(`/todos/${todoId}/tags/${tagId}`),
    onSuccess: refreshTagAndTodoQueries,
  });

export const useDetachTag = () =>
  useMutation({
    mutationFn: ({ todoId, tagId }: { todoId: string; tagId: string }) =>
      api.delete(`/todos/${todoId}/tags/${tagId}`),
    onSuccess: refreshTagAndTodoQueries,
  });
