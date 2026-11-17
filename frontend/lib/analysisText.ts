export function formatPeriod(value: unknown, locale: string): string {
  return String(value ?? '').replace(/\b([1-4])[TQ](?=\b|\/)/gi, `$1${locale === 'en' ? 'Q' : 'T'}`);
}

// Return text segments instead of HTML so report content remains escaped by React.
export function splitBold(text: string): { text: string; bold: boolean }[] {
  return text.split(/(\*\*[\s\S]+?\*\*)/g).map(part => ({
    text: part.startsWith('**') && part.endsWith('**') && part.length > 4 ? part.slice(2, -2) : part,
    bold: part.startsWith('**') && part.endsWith('**') && part.length > 4,
  }));
}

export type AnalysisBlock = { kind: 'text'; text: string } | { kind: 'table'; header: string[]; rows: string[][] };

// Split Markdown pipe tables out of analysis prose so they render as real tables.
export function splitTables(text: string): AnalysisBlock[] {
  const blocks: AnalysisBlock[] = [];
  let prose: string[] = [];
  let table: string[][] = [];
  const cells = (line: string) => line.trim().replace(/^\||\|$/g, '').split('|').map(cell => cell.trim());
  const flushProse = () => { if (prose.length) blocks.push({ kind: 'text', text: prose.join('\n') }); prose = []; };
  const flushTable = () => {
    if (table.length > 1) blocks.push({ kind: 'table', header: table[0], rows: table.slice(1) });
    else if (table.length) prose.push(...table.map(row => `| ${row.join(' | ')} |`));
    table = [];
  };
  for (const line of text.split('\n')) {
    const trimmed = line.trim();
    if (trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.length > 1) {
      if (!table.length) flushProse();
      const row = cells(trimmed);
      if (!row.every(cell => /^:?-+:?$/.test(cell))) table.push(row);
    } else {
      if (table.length) flushTable();
      prose.push(line);
    }
  }
  flushTable();
  flushProse();
  return blocks;
}
