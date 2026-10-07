<script lang="ts">
  import SearchInput from "../lib/kit/components/SearchInput.svelte";
  import Table from "../lib/kit/components/Table.svelte";
  import TableHeaderCell from "../lib/kit/components/TableHeaderCell.svelte";
  import { display, formatTimestamp } from "../lib/format";
  import type { HistoryEntry } from "../lib/types";

  interface Props { entries: HistoryEntry[]; loading: boolean; error: string; oninspect?: (taskId: string) => void }
  let { entries, loading, error, oninspect = () => undefined }: Props = $props();
  const pageSize = 25;
  let page = $state(0);
  let query = $state("");
  const filtered = $derived.by(() => {
    const needle = query.trim().toLowerCase();
    return needle ? entries.filter((entry) => [entry.title, entry.kind, entry.detail, entry.task_id].some((part) => part?.toLowerCase().includes(needle))) : entries;
  });
  const pageCount = $derived(Math.max(1, Math.ceil(filtered.length / pageSize)));
  const visible = $derived(filtered.slice(page * pageSize, (page + 1) * pageSize));
  $effect(() => { query; page = 0; });
</script>

<section class="page-view history-view" data-testid="history-view" aria-labelledby="history-title">
  <div class="page-heading">
    <div><p class="eyebrow">LOCAL EVIDENCE / RECORDED OUTCOMES</p><h1 id="history-title">History<span class="heading-period">.</span></h1><p class="page-subtitle">What Snooze has recorded, with missing usage and validation fields called out.</p></div>
    <div class="history-total"><strong>{entries.length.toLocaleString()}</strong><span>available records</span></div>
  </div>
  <div class="history-provenance"><span class="provenance-mark">i</span><p><strong>Source: local Snooze history.</strong> Provider tokens, credit usage, cost and rich validation analytics have not been imported. Missing values remain unavailable.</p></div>
  {#if error}<p class="stale-banner" role="status">History refresh failed. Previously loaded records remain visible. {error}</p>{/if}
  <div class="history-toolbar"><SearchInput bind:value={query} placeholder="Find a task or recorded event" ariaLabel="Search history" block /><span>{loading ? "Refreshing records…" : "Usage analytics unavailable"}</span></div>
  <div class="queue-results-bar"><span>Showing {filtered.length ? page * pageSize + 1 : 0}–{Math.min((page + 1) * pageSize, filtered.length)} of {filtered.length.toLocaleString()} records</span><span>Latest available evidence first</span></div>
  <div class="history-table-frame">
    <Table ariaLabel="Snooze history records" class="history-table">
      {#snippet header()}<TableHeaderCell label="Recorded" /><TableHeaderCell label="Outcome / event" /><TableHeaderCell label="Task" /><TableHeaderCell label="Evidence and coverage" />{/snippet}
      {#snippet children()}
        {#each visible as entry (entry.id)}
          <tr data-testid="history-row">
            <td class="mono history-date">{formatTimestamp(entry.at)}</td>
            <td><span class="history-kind" data-kind={entry.kind}>{entry.kind}</span></td>
            <td><strong>{entry.title}</strong>{#if entry.task_id}<small class="table-subline mono">{entry.task_id}</small>{/if}</td>
            <td class="history-detail">{entry.detail}{#if entry.task_id}<button type="button" class="history-inspect" onclick={() => oninspect(entry.task_id!)}>Inspect</button>{/if}</td>
          </tr>
        {/each}
      {/snippet}
    </Table>
    {#if !visible.length}<div class="empty-table"><strong>{query ? "No records match this search" : "No local history is available"}</strong><span>Nothing is counted as zero when Snooze has no source data.</span></div>{/if}
  </div>
  <div class="pagination"><span>Page {page + 1} of {pageCount}</span><div><button class="page-button kit-control-states" type="button" aria-label="Previous page" disabled={page === 0} onclick={() => (page = Math.max(0, page - 1))}>‹</button><button class="page-button kit-control-states" type="button" aria-label="Next page" disabled={page >= pageCount - 1} onclick={() => (page = Math.min(pageCount - 1, page + 1))}>›</button></div></div>
</section>
