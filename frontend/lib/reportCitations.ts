type Source = { id: string };

function citationId(marker: string, sources: Source[]) {
  return sources.find(source => source.id === marker)?.id
    || (/^[1-9]\d*$/.test(marker) ? sources[Number(marker) - 1]?.id : undefined);
}

export function reportCitationIds(value: string, sources: Source[]) {
  return [...new Set([...value.matchAll(/\[([^\]\n]+)\]/g)].flatMap(match =>
    match[1].split(/\s*[,;]\s*/).map(marker => citationId(marker.trim(), sources)).filter((id): id is string => !!id)
  ))];
}

export function stripReportCitations(value: string, sources: Source[]) {
  return value.replace(/\[([^\]\n]+)\]/g, (match, contents: string) =>
    contents.split(/\s*[,;]\s*/).every(marker => citationId(marker.trim(), sources) || /^[SF]\d+$/i.test(marker.trim())) ? "" : match
  ).replace(/ +([,.;:!?])/g, "$1").replace(/ {2,}/g, " ").trim();
}
