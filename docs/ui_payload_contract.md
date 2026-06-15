# RLA 2 — UI Payload Contract



## Source



The compact dashboard payload is produced by:



```python

get_dashboard_compact_payload(limit=50, recent_limit=10)

```



To inspect it from the terminal:



```bash

python -m rla_app.api.print_dashboard_compact_payload_dev 50 10

```



\---



## Top-Level Shape



| Key                      | Type            | Description                                      |

|--------------------------|-----------------|--------------------------------------------------|

| `app`                    | `AppInfo`       | App name and version                             |

| `database`               | `DatabaseInfo`  | Path to active SQLite database                   |

| `summary`                | `DashboardSummary` | Totals from loaded matches                    |

| `snapshot`               | `SessionSnapshot` | Metrics for the active session (gap â‰¤ 2h)      |

| `session_summary`        | `SessionSummary` | Human-friendly session card data                |

| `system_status`          | `SystemStatus`  | Overall system state for top-level UI indicator  |

| `metric_cards`           | `MetricCard\[]`  | Dashboard cards ready to render                  |

| `active_session_matches` | `MatchItem\[]`   | Matches within the current active session        |

| `recent_matches`         | `MatchItem\[]`   | Last N matches by real date (descending)         |



\---



## TypeScript Interfaces



```ts

type CardTone = "neutral" | "success" | "warning";



interface AppInfo {

&#x20; name: string;

&#x20; version: string;

}



interface DatabaseInfo {

&#x20; path: string;

}



interface DashboardSummary {

&#x20; total_loaded: number;

&#x20; metadata_ready: number;

&#x20; metadata_missing: number;

&#x20; latest_match_date: string | null;

}



interface SessionSnapshot {

&#x20; loaded_matches: number;

&#x20; total_matches: number;

&#x20; metadata_ready: number;

&#x20; metadata_missing: number;

&#x20; latest_day: string | null;

&#x20; matches_on_latest_day: number;

&#x20; online_matches: number;

&#x20; private_matches: number;

&#x20; other_match_types: number;

&#x20; most_played_map: string | null;

&#x20; most_common_team_size: number | null;

&#x20; total_seconds: number;

&#x20; total_minutes_label: string;

&#x20; average_match_seconds: number | null;

&#x20; average_match_minutes_label: string;

&#x20; session_start: string | null;

&#x20; session_end: string | null;

&#x20; session_gap_hours: number;

}



interface SessionSummary {

&#x20; title: string;

&#x20; match_count: number;

&#x20; session_start: string | null;

&#x20; session_end: string | null;

&#x20; total_minutes_label: string;

&#x20; average_match_minutes_label: string;

&#x20; most_played_map: string | null;

&#x20; most_played_display_map: string | null;

&#x20; most_common_team_size: number | null;

&#x20; unique_maps: string\[];

&#x20; unique_display_maps: string\[];

&#x20; match_types: string\[];

&#x20; team_sizes: number\[];

&#x20; latest_map: string | null;

&#x20; latest_display_map: string | null;

&#x20; latest_match_type: string | null;

&#x20; latest_score_label: string | null;

}



interface SystemStatus {

&#x20; state: "Ready" | "Partial" | "Awaiting replay";

&#x20; message: string;

&#x20; has_matches: boolean;

&#x20; has_active_session: boolean;

&#x20; total_loaded: number;

&#x20; metadata_ready: number;

&#x20; metadata_missing: number;

&#x20; latest_match_date: string | null;

&#x20; latest_map: string | null;

&#x20; latest_display_map: string | null;

&#x20; latest_match_type: string | null;

&#x20; latest_parse_level: string | null;

&#x20; latest_metadata_ready: boolean;

&#x20; active_session_count: number;

}



interface MetricCard {

&#x20; id: string;

&#x20; label: string;

&#x20; value: string;

&#x20; sublabel: string;

&#x20; tone: CardTone;

}



interface MatchItem {

&#x20; id: number;

&#x20; file_name: string;

&#x20; status: string | null;

&#x20; parse_status: string | null;

&#x20; parse_level: string | null;

&#x20; meta_status: string | null;

&#x20; date: string | null;

&#x20; map_name: string | null;

&#x20; display_map_name: string;

&#x20; short_map_name: string;

&#x20; map_family: string | null;

&#x20; map_variant: string | null;

&#x20; map_name_source: string;

&#x20; match_type: string | null;

&#x20; team_size: number | null;

&#x20; team0_score: number | null;

&#x20; team1_score: number | null;

&#x20; total_seconds_played: number | null;

&#x20; replay_name: string | null;

&#x20; score_label: string;

&#x20; seconds_label: string;

&#x20; metadata_ready: boolean;

}



interface DashboardCompactPayload {

&#x20; app: AppInfo;

&#x20; database: DatabaseInfo;

&#x20; summary: DashboardSummary;

&#x20; snapshot: SessionSnapshot;

&#x20; session_summary: SessionSummary;

&#x20; system_status: SystemStatus;

&#x20; metric_cards: MetricCard\[];

&#x20; active_session_matches: MatchItem\[];

&#x20; recent_matches: MatchItem\[];

}

```



\---



## UI Notes



\- \*\*Do not calculate W/L yet.\*\* Team assignment is not known; `score_label` is a neutral scoreboard (e.g. `"2-3"`), not a result for the user.

\- Use `display_map_name` for all visible map labels in the UI. Preserve `map_name` for raw data / debug panels only.

\- `active_session_matches` contains only matches within the current session (gap â‰¤ 2h). Use this for the "Current Session" card.

\- `recent_matches` is the last N matches by real match date (descending). Use this for the match history list.

\- `system_status.state` drives the main top-level indicator:

&#x20; - `"Ready"` â†’ all loaded replays have metadata.

&#x20; - `"Partial"` â†’ some replays are missing metadata.

&#x20; - `"Awaiting replay"` â†’ no replays found yet.

\- `metric_cards` is pre-built and ordered. Render them directly without recomputing values in the frontend.

\- `map_name_source` can be `"known"`, `"fallback"`, or `"missing"` — useful for debug badges.



\---



## Example Usage in React



```tsx

import type { DashboardCompactPayload, MetricCard, MatchItem } from "./types";



function Dashboard({ payload }: { payload: DashboardCompactPayload }) {

&#x20; return (

&#x20;   <div>

&#x20;     {/\* Metric cards \*/}

&#x20;     <div className="cards-row">

&#x20;       {payload.metric_cards.map((card: MetricCard) => (

&#x20;         <MetricCardWidget key={card.id} card={card} />

&#x20;       ))}

&#x20;     </div>



&#x20;     {/\* Active session \*/}

&#x20;     <section>

&#x20;       <h2>{payload.session_summary.title}</h2>

&#x20;       <p>{payload.session_summary.match_count} matches Â· {payload.session_summary.total_minutes_label} min</p>

&#x20;       <p>Maps played: {payload.session_summary.unique_display_maps.join(", ")}</p>

&#x20;     </section>



&#x20;     {/\* Recent matches \*/}

&#x20;     <ul>

&#x20;       {payload.recent_matches.map((m: MatchItem) => (

&#x20;         <li key={m.id}>

&#x20;           {m.date} Â· {m.display_map_name} Â· {m.match_type} Â· {m.score_label}

&#x20;         </li>

&#x20;       ))}

&#x20;     </ul>

&#x20;   </div>

&#x20; );

}

```


