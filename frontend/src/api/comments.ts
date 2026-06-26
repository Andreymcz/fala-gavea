const BASE_URL = (import.meta.env.VITE_API_URL as string) || "";

export interface Comment {
  id: string;
  forwarding_id: string;
  // null for unauthenticated/public viewers — the API hides the author from the public.
  author_id: string | null;
  text: string;
  created_at: string;
}

export async function listComments(forwardingId: string): Promise<Comment[]> {
  const res = await fetch(`${BASE_URL}/forwardings/${forwardingId}/comments`);
  if (!res.ok) throw new Error("Failed to fetch comments");
  return res.json();
}

export async function addComment(
  forwardingId: string,
  text: string,
  token: string,
): Promise<Comment> {
  const res = await fetch(`${BASE_URL}/forwardings/${forwardingId}/comments`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error("Failed to add comment");
  return res.json();
}

export async function deleteComment(
  forwardingId: string,
  commentId: string,
  token: string,
): Promise<void> {
  const res = await fetch(
    `${BASE_URL}/forwardings/${forwardingId}/comments/${commentId}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!res.ok && res.status !== 404) throw new Error("Failed to delete comment");
}
