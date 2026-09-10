// src/components/SearchPanel.jsx
import { useEffect, useState } from "react";

export default function SearchPanel({ endpoint, defaultFilters }) {
  const [results, setResults] = useState([]);
  const [filters, setFilters] = useState(defaultFilters ?? { tag: null, page: 1 });
  const [status, setStatus] = useState("idle");

  useEffect(() => {
    setStatus("loading");
    fetch(`${endpoint}?${new URLSearchParams({ ...filters })}`)
      .then((r) => r.json())
      .then((data) => {
        setResults(data.items);
        setFilters({ ...filters, total: data.total });
        setStatus("done");
      });
  }, [endpoint, filters, results]);

  return (
    <div>
      <input onChange={(e) => setFilters({ ...filters, tag: e.target.value })} />
      <span>{status}</span>
      <ul>
        {results.map((r) => (
          <li key={r.id}>{r.title}</li>
        ))}
      </ul>
    </div>
  );
}
