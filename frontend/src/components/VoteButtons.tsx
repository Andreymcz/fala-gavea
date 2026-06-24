import type { VoteSummary } from "@/lib/types";

interface Props {
  summary: VoteSummary | null;
  onVote: (value: 1 | -1) => void;
  onRetract: () => void;
  disabled?: boolean;
  readOnly?: boolean;
  loading?: boolean;
}

export function VoteButtons({ summary, onVote, onRetract, disabled, readOnly, loading }: Props) {
  if (disabled) return null;

  const userVote = summary?.user_vote ?? null;

  function handleClick(value: 1 | -1) {
    if (readOnly || loading) return;
    if (userVote === value) onRetract();
    else onVote(value);
  }

  const upClass = userVote === 1 ? "bg-green-100 text-green-700 font-semibold" : "bg-gray-100 text-gray-600";
  const downClass = userVote === -1 ? "bg-red-100 text-red-700 font-semibold" : "bg-gray-100 text-gray-600";

  return (
    <div className="flex items-center gap-1 text-sm">
      <button
        type="button"
        onClick={() => handleClick(1)}
        disabled={readOnly || loading}
        className={`flex items-center gap-0.5 rounded px-1.5 py-0.5 transition-colors text-xs ${upClass} ${!readOnly ? "hover:bg-green-50" : "cursor-default"}`}
        aria-label="Votar a favor"
      >
        ▲ {summary?.upvotes ?? 0}
      </button>
      <button
        type="button"
        onClick={() => handleClick(-1)}
        disabled={readOnly || loading}
        className={`flex items-center gap-0.5 rounded px-1.5 py-0.5 transition-colors text-xs ${downClass} ${!readOnly ? "hover:bg-red-50" : "cursor-default"}`}
        aria-label="Votar contra"
      >
        ▼ {summary?.downvotes ?? 0}
      </button>
    </div>
  );
}
