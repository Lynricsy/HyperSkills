'use client';

import {useState} from 'react';
import {ResultsTable} from './ResultsTable';
import {FilterSidebar} from './FilterSidebar';
import {ExpensiveChart} from './ExpensiveChart';

export function SearchPanel({rows}: {rows: Row[]}) {
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<string[]>([]);

  const visible = rows.filter(row =>
    row.name.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <div className="grid grid-cols-[240px_1fr]">
      <FilterSidebar selected={selected} onChange={setSelected} />
      <div>
        <input value={query} onChange={e => setQuery(e.target.value)} />
        <ExpensiveChart rows={rows} />
        <ResultsTable rows={visible} />
      </div>
    </div>
  );
}

export type Row = {id: string; name: string; total: number};
