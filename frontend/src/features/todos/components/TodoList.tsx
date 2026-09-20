import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import type { Todo } from "../api/todos";
import { useDeleteTodo, useToggleTodo } from "../api/todos";
import type { Tag } from "../api/tags";

interface TodoListProps {
  todos: Todo[];
  selected: Set<string>;
  onSelect: (id: string) => void;
  tags: Tag[];
  onAttachTag: (todoId: string, tagId: string) => void;
  onDetachTag: (todoId: string, tagId: string) => void;
}

export function TodoList({ todos, selected, onSelect, tags, onAttachTag, onDetachTag }: TodoListProps) {
  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();

  const handleToggle = (todo: Todo) => {
    toggleTodo.mutate(todo);
  };

  const handleEdit = (todo: Todo) => {
    setEditingTodo(todo);
  };

  const handleDelete = (id: string) => {
    deleteTodo.mutate(id);
  };

  if (todos.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">No todos yet</p>
        <p className="text-sm mt-1">Create your first todo to get started</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-2">
        {todos.map((todo, index) => (
          <TodoItem
            key={index}
            todo={todo}
            index={index}
            onToggle={handleToggle}
            onEdit={handleEdit}
            onDelete={handleDelete}
            selected={selected.has(todo.id)} onSelect={onSelect} tags={tags} onAttachTag={onAttachTag} onDetachTag={onDetachTag}
          />
        ))}
      </div>

      {editingTodo && (
        <TodoForm
          mode="edit"
          todo={editingTodo}
          open={!!editingTodo}
          onClose={() => setEditingTodo(null)}
        />
      )}
    </>
  );
}
