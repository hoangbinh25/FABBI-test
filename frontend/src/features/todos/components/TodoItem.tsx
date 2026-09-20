import { Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import type { Tag } from "../api/tags";
import type { Todo } from "../api/todos";

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

export function TodoItem({
  todo,
  onToggle,
  onEdit,
  onDelete,
  selected,
  onSelect,
  tags = [],
  onAttachTag,
  onDetachTag,
}: TodoItemProps) {
  const assignedTags = todo.tags ?? [];
  const availableTags = tags.filter(
    (tag) => !assignedTags.some((assigned) => assigned.id === tag.id),
  );

  return (
    <div className="group flex items-center gap-3 rounded-lg border bg-card p-3 transition-colors hover:bg-accent/50">
      <Checkbox
        checked={selected}
        aria-label={`Select ${todo.title}`}
        onCheckedChange={() => onSelect?.(todo.id)}
      />
      <Checkbox
        id={`todo-${todo.id}`}
        checked={todo.completed}
        onCheckedChange={() => onToggle(todo)}
      />

      <div className="min-w-0 flex-1">
        <label
          htmlFor={`todo-${todo.id}`}
          className={`cursor-pointer text-sm font-medium ${
            todo.completed ? "text-muted-foreground line-through" : ""
          }`}
        >
          {todo.title}
        </label>
        {todo.description && (
          <p className="mt-0.5 truncate text-xs text-muted-foreground">
            {todo.description}
          </p>
        )}
        <div className="mt-1 flex flex-wrap gap-1">
          {assignedTags.map((tag) => (
            <span
              key={tag.id}
              className="rounded px-1.5 text-xs"
              style={{ backgroundColor: tag.color || "#e5e7eb" }}
            >
              {tag.name}
              {onDetachTag && (
                <button
                  className="ml-1"
                  aria-label={`Remove ${tag.name}`}
                  onClick={() => onDetachTag(todo.id, tag.id)}
                >
                  ×
                </button>
              )}
            </span>
          ))}
          {onAttachTag &&
            availableTags.map((tag) => (
              <button
                key={tag.id}
                className="text-xs text-muted-foreground"
                onClick={() => onAttachTag(todo.id, tag.id)}
              >
                +{tag.name}
              </button>
            ))}
        </div>
      </div>

      <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => onEdit(todo)}>
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
