import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/auth/AuthContext";
import { listComments, addComment, deleteComment, type Comment } from "@/api/comments";

interface Props {
  forwardingId: string;
}

export function CommentSection({ forwardingId }: Props) {
  const { token, user } = useAuth();
  const qc = useQueryClient();
  const [text, setText] = useState("");

  const { data: comments = [], isLoading } = useQuery({
    queryKey: ["comments", forwardingId],
    queryFn: () => listComments(forwardingId),
    staleTime: 30_000,
  });

  const addMutation = useMutation({
    mutationFn: () => addComment(forwardingId, text.trim(), token!),
    onSuccess: () => {
      setText("");
      qc.invalidateQueries({ queryKey: ["comments", forwardingId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (commentId: string) => deleteComment(forwardingId, commentId, token!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["comments", forwardingId] });
    },
  });

  function canDelete(comment: Comment): boolean {
    if (!user) return false;
    if (comment.author_id && user.id === comment.author_id) return true;
    if (user.role === "agent" || user.role === "admin") return true;
    return false;
  }

  const textValid = text.trim().length >= 1 && text.trim().length <= 500;

  return (
    <div className="mt-4 space-y-3">
      <h4 className="text-sm font-semibold text-gray-700">Comentários</h4>
      {isLoading ? (
        <p className="text-xs text-gray-400">Carregando comentários...</p>
      ) : comments.length === 0 ? (
        <p className="text-xs text-gray-400">Nenhum comentário ainda.</p>
      ) : (
        <ul className="space-y-2">
          {comments.map((c) => (
            <li key={c.id} className="rounded border border-gray-100 bg-gray-50 px-3 py-2 text-sm">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="font-mono text-xs text-gray-500">{c.author_id ? c.author_id.slice(0, 8) : "Anônimo"}</span>
                  <span className="ml-2 text-xs text-gray-400">
                    {new Date(c.created_at).toLocaleDateString("pt-BR")}
                  </span>
                </div>
                {canDelete(c) && (
                  <button
                    type="button"
                    onClick={() => deleteMutation.mutate(c.id)}
                    className="text-gray-400 hover:text-red-500 text-xs"
                    aria-label="Excluir comentário"
                  >
                    🗑
                  </button>
                )}
              </div>
              <p className="mt-1 text-gray-700">{c.text}</p>
            </li>
          ))}
        </ul>
      )}
      {token && (
        <div className="flex gap-2">
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={500}
            placeholder="Adicione um comentário sobre este encaminhamento..."
            className="flex-1 rounded border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
          <button
            type="button"
            onClick={() => addMutation.mutate()}
            disabled={!textValid || addMutation.isPending}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white disabled:opacity-50 hover:bg-blue-700"
          >
            Comentar
          </button>
        </div>
      )}
    </div>
  );
}
