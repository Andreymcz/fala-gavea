import type { VoteSummary } from "@/lib/types";

interface Props {
  summary: VoteSummary | null;
  onVote: (value: 1 | -1) => void;
  onRetract: () => void;
  disabled?: boolean;
  loading?: boolean;
}

export function VoteButtons({ summary, onVote, onRetract, disabled, loading }: Props) {
  if (disabled) return null;

  const userVote = summary?.user_vote ?? null;

  function handleClick(value: 1 | -1) {
    if (loading) return;
    if (userVote === value) {
      onRetract();
    } else {
      onVote(value);
    }
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <button
        type="button"
        onClick={() => handleClick(1)}
        disabled={loading}
        className={`flex items-center gap-1 rounded px-2 py-1 transition-colors ${
          userVote === 1
            ? "bg-green-100 text-green-700 font-semibold"
            : "bg-gray-100 text-gray-600 hover:bg-green-50"
        }`}
        aria-label="Votar a favor"
      >
        ▲ {summary?.upvotes ?? 0}
      </button>
      <button
        type="button"
        onClick={() => handleClick(-1)}
        disabled={loading}
        className={`flex items-center gap-1 rounded px-2 py-1 transition-colors ${
          userVote === -1
            ? "bg-red-100 text-red-700 font-semibold"
            : "bg-gray-100 text-gray-600 hover:bg-red-50"
        }`}
        aria-label="Votar contra"
      >
        ▼ {summary?.downvotes ?? 0}
      </button>
    </div>
  );
}
