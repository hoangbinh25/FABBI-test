import { useState } from "react";
import type { Tag } from "../api/tags";
import { useDeleteTodo, useToggleTodo, type Todo } from "../api/todos";
import { TodoForm } from "./TodoForm";
import { TodoItem } from "./TodoItem";

interface TodoListProps {
  todos: Todo[];
  selected: Set<string>;
  onSelect: (id: string) => void;
  tags: Tag[];
  onAttachTag: (todoId: string, tagId: string) => void;
  onDetachTag: (todoId: string, tagId: string) => void;
}

export function TodoList({
  todos,
  selected,
  onSelect,
  tags,
  onAttachTag,
  onDetachTag,
}: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();

  if (todos.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        <p className="text-lg">No todos yet</p>
        <p className="mt-1 text-sm">Create your first todo to get started</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-2">
        {todos.map((todo, index) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            index={index}
            onToggle={(item) => toggleTodo.mutate(item)}
            onEdit={setEditingTodo}
            onDelete={(id) => deleteTodo.mutate(id)}
            selected={selected.has(todo.id)}
            onSelect={onSelect}
            tags={tags}
            onAttachTag={onAttachTag}
            onDetachTag={onDetachTag}
          />
        ))}
      </div>

      {editingTodo && (
        <TodoForm
          mode="edit"
          todo={editingTodo}
          open
          onClose={() => setEditingTodo(null)}
        />
      )}
    </>
  );
}
