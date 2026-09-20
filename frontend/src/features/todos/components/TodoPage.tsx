import { useState } from "react";
import { LogOut, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { type Tag, useAttachTag, useDeleteTag, useDetachTag, useTags } from "../api/tags";
import { type TodoFilters, useBulkStatus, useTodos } from "../api/todos";
import { TagEditDialog } from "./TagEditDialog";
import { TagForm } from "./TagForm";
import { TodoForm } from "./TodoForm";
import { TodoList } from "./TodoList";

export function TodoPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [filters, setFilters] = useState<TodoFilters>({});
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const { data, isLoading, error } = useTodos(filters);
  const { data: tags = [] } = useTags();
  const { user, logout } = useAuth();
  const bulkStatus = useBulkStatus();
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();
  const deleteTag = useDeleteTag();

  const updateFilters = (next: Partial<TodoFilters>) => {
    setFilters((current) => ({ ...current, ...next }));
    setSelected(new Set());
  };

  const toggleSelection = (todoId: string) => {
    setSelected((current) => {
      const next = new Set(current);
      next.has(todoId) ? next.delete(todoId) : next.add(todoId);
      return next;
    });
  };

  const applyBulkStatus = (completed: boolean) => {
    bulkStatus.mutate(
      { ids: [...selected], completed },
      { onSuccess: () => setSelected(new Set()) },
    );
  };

  return (
    <div className="min-h-screen bg-muted/40">
      <header className="bg-card border-b">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">Todo App</h1>
            {user && <p className="text-sm text-muted-foreground">{user.email}</p>}
          </div>
          <Button variant="ghost" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4 mr-2" />Logout
          </Button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">My Todos</CardTitle>
            <Button size="sm" onClick={() => setShowCreateForm(true)}>
              <Plus className="h-4 w-4 mr-1" />Add Todo
            </Button>
          </CardHeader>
          <Separator />
          <CardContent className="pt-4 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <Input placeholder="Search title" value={filters.keyword ?? ""} onChange={(event) => updateFilters({ keyword: event.target.value || undefined })} />
              <select className="border rounded px-2" value={filters.status ?? ""} onChange={(event) => updateFilters({ status: (event.target.value || undefined) as TodoFilters["status"] })}>
                <option value="">All statuses</option><option value="active">Active</option><option value="completed">Completed</option>
              </select>
              <select className="border rounded px-2" value={filters.tag_id ?? ""} onChange={(event) => updateFilters({ tag_id: event.target.value || undefined })}>
                <option value="">All tags</option>{tags.map((tag) => <option key={tag.id} value={tag.id}>{tag.name}</option>)}
              </select>
              <Input type="date" value={filters.date_from ?? ""} onChange={(event) => updateFilters({ date_from: event.target.value || undefined })} />
              <Input type="date" value={filters.date_to ?? ""} onChange={(event) => updateFilters({ date_to: event.target.value || undefined })} />
              <Button variant="outline" onClick={() => { setFilters({}); setSelected(new Set()); }}>Clear filters</Button>
            </div>

            <div className="flex flex-wrap gap-2 items-center">
              <TagForm />
              {tags.map((tag) => <span key={tag.id} className="rounded border px-2 py-1 text-xs" style={{ borderColor: tag.color || undefined }}>
                {tag.name}<button className="ml-1" onClick={() => setEditingTag(tag)}>Edit</button><button className="ml-1" onClick={() => deleteTag.mutate(tag.id)}>×</button>
              </span>)}
            </div>

            {selected.size > 0 && <div className="flex gap-2"><span className="text-sm self-center">{selected.size} selected</span><Button size="sm" onClick={() => applyBulkStatus(true)}>Mark completed</Button><Button size="sm" variant="outline" onClick={() => applyBulkStatus(false)}>Mark active</Button></div>}
            {isLoading && <div className="text-center py-12 text-muted-foreground">Loading todos...</div>}
            {error && <div className="text-center py-12 text-destructive">Failed to load todos. Please try again.</div>}
            {data && <TodoList todos={data.items} selected={selected} onSelect={toggleSelection} tags={tags} onAttachTag={(todoId, tagId) => attachTag.mutate({ todoId, tagId })} onDetachTag={(todoId, tagId) => detachTag.mutate({ todoId, tagId })} />}
            {data && data.total > 0 && <div className="text-center text-sm text-muted-foreground">Showing {data.items.length} of {data.total} todos</div>}
          </CardContent>
        </Card>
      </main>
      <TodoForm mode="create" open={showCreateForm} onClose={() => setShowCreateForm(false)} />
      <TagEditDialog tag={editingTag} onClose={() => setEditingTag(null)} />
    </div>
  );
}
