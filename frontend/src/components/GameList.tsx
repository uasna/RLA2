import React from "react";
import type { MatchItem } from "../types/dashboardPayload";

interface GameListProps {
  matches: MatchItem[];
}

export default function GameList({ matches }: GameListProps) {
  return (
    <div className="game-list">
      {matches.map((match) => (
        <div className="game-row" key={match.id}>
          <span className="game-map">{match.display_map_name}</span>
          <span className="game-type">{match.match_type ?? "—"}</span>
          <span className="game-score">{match.score_label}</span>
          <span className="game-secs">{match.seconds_label} min</span>
        </div>
      ))}
    </div>
  );
}