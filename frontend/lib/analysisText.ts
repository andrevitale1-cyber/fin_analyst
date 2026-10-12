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
