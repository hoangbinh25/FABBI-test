import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";

export interface Tag { id: string; name: string; color: string | null; }
const refresh = () => { queryClient.invalidateQueries({ queryKey: ["tags"] }); queryClient.invalidateQueries({ queryKey: ["todos"] }); };
export const useTags = () => useQuery({ queryKey: ["tags"], queryFn: async (): Promise<Tag[]> => (await api.get("/tags")).data });
export const useCreateTag = () => useMutation({ mutationFn: (data: {name: string; color?: string}) => api.post("/tags", data), onSuccess: refresh });
export const useDeleteTag = () => useMutation({ mutationFn: (id: string) => api.delete(`/tags/${id}`), onSuccess: refresh });
export const useUpdateTag = () => useMutation({ mutationFn: ({ id, name, color }: { id: string; name: string; color?: string }) => api.patch(`/tags/${id}`, { name, color }), onSuccess: refresh });
export const useAttachTag = () => useMutation({ mutationFn: ({todoId, tagId}: {todoId: string; tagId: string}) => api.post(`/todos/${todoId}/tags/${tagId}`), onSuccess: refresh });
export const useDetachTag = () => useMutation({ mutationFn: ({todoId, tagId}: {todoId: string; tagId: string}) => api.delete(`/todos/${todoId}/tags/${tagId}`), onSuccess: refresh });
