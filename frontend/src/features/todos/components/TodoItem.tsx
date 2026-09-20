import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2 } from "lucide-react";
import type { Todo } from "../api/todos";
import type { Tag } from "../api/tags";

interface TodoItemProps {
  todo: Todo;
  index: number;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
  selected?: boolean;
  onSelect?: (id: string) => void;
  tags?: Tag[];
  onAttachTag?: (todoId: string, tagId: string) => void;
  onDetachTag?: (todoId: string, tagId: string) => void;
}

export function TodoItem({ todo, onToggle, onEdit, onDelete, selected, onSelect, tags = [], onAttachTag, onDetachTag }: TodoItemProps) {
  const assignedTags = todo.tags ?? [];

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors group">
      <Checkbox checked={selected} onCheckedChange={() => onSelect?.(todo.id)} aria-label={`Select ${todo.title}`} />
      <Checkbox
        id={`todo-${todo.id}`}
        checked={todo.completed}
        onCheckedChange={() => onToggle(todo)}
      />

      <div className="flex-1 min-w-0">
        <label
          htmlFor={`todo-${todo.id}`}
          className={`text-sm font-medium cursor-pointer ${
            todo.completed ? "line-through text-muted-foreground" : ""
          }`}
        >
          {todo.title}
        </label>
        {todo.description && (
          <p className="text-xs text-muted-foreground mt-0.5 truncate">
            {todo.description}
          </p>
        )}
        <div className="flex flex-wrap gap-1 mt-1">
          {assignedTags.map((tag) => <span key={tag.id} className="rounded px-1.5 text-xs" style={{ backgroundColor: tag.color || "#e5e7eb" }}>{tag.name}{onDetachTag && <button className="ml-1" aria-label={`Remove ${tag.name}`} onClick={() => onDetachTag(todo.id, tag.id)}>×</button>}</span>)}
          {onAttachTag && tags.filter((tag) => !assignedTags.some((assigned) => assigned.id === tag.id)).map((tag) => <button key={tag.id} className="text-xs text-muted-foreground" onClick={() => onAttachTag(todo.id, tag.id)}>+{tag.name}</button>)}
        </div>
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => onEdit(todo)}
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-destructive hover:text-destructive"
          onClick={() => onDelete(todo.id)}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
