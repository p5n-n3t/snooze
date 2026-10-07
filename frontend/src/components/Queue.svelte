<script lang="ts">
  import SearchInput from "../lib/kit/components/SearchInput.svelte";
  import SelectDropdown from "../lib/kit/components/SelectDropdown.svelte";
  import Table from "../lib/kit/components/Table.svelte";
  import TableHeaderCell from "../lib/kit/components/TableHeaderCell.svelte";
  import Button from "../lib/kit/components/Button.svelte";
  import ChevronLeftIcon from "@lucide/svelte/icons/chevron-left";
  import ChevronRightIcon from "@lucide/svelte/icons/chevron-right";
  import { display, formatTimestamp, slotIsActive } from "../lib/format";
  import type { DashboardState, Slot } from "../lib/types";

  interface Props { dashboard: DashboardState; oninspect: (taskId: string) => void }
  let { dashboard, oninspect }: Props = $props();

  let query = $state("");
  let statusFilter = $state("all");
  let page = $state(0);
  const pageSize = 25;
  const statusOptions = [
    { value: "all", label: "All active states" },
    { value: "running", label: "Running" },
    { value: "queued", label: "Queued" },
    { value: "waiting", label: "Waiting" },
  ];
  const filtered = $derived.by(() => {
    const needle = query.trim().toLowerCase();
    return dashboard.slots.filter((slot) => {
      if (!slotIsActive(slot)) return false;
      if (statusFilter !== "all" && (slot.task_state ?? "").toLowerCase() !== statusFilter) return false;
      if (!needle) return true;
      return [slot.task_id, slot.task_summary, slot.account_id, slot.workspace_id, slot.confirmed_model]
        .some((value) => value?.toLowerCase().includes(needle));
    });
  });
  const pageCount = $derived(Math.max(1, Math.ceil(filtered.length / pageSize)));
  const visible = $derived(filtered.slice(page * pageSize, (page + 1) * pageSize));
  $effect(() => { query; statusFilter; page = 0; });
  const actionReason = "This action is not supported by the current Snooze control API.";

  function changePage(next: number) { page = Math.min(Math.max(0, next), pageCount - 1); }
</script>

<section class="page-view queue-view" data-testid="queue-view" aria-labelledby="queue-title">
  <div class="page-heading">
    <div><p class="eyebrow">ASSIGNMENTS / BOUNDED VIEW</p><h1 id="queue-title">Queue<span class="heading-period">.</span></h1><p class="page-subtitle">Search occupied assignments and inspect their current evidence.</p></div>
    <div class="queue-total"><strong>{filtered.length.toLocaleString()}</strong><span>active assignments</span></div>
  </div>
  <div class="queue-toolbar">
    <SearchInput bind:value={query} placeholder="Search task, account or workspace" ariaLabel="Search assignments" block class="queue-search" />
    <SelectDropdown value={statusFilter} options={statusOptions} onchange={(value) => (statusFilter = value)} title="Task state" />
  </div>
  <div class="queue-results-bar"><span>Showing {filtered.length ? page * pageSize + 1 : 0}–{Math.min((page + 1) * pageSize, filtered.length)} of {filtered.length.toLocaleString()} assignments</span><span>Terminal sessions appear in History</span></div>
  <div class="queue-table-frame">
    <Table ariaLabel="Active Snooze assignments" class="queue-table">
      {#snippet header()}<TableHeaderCell label="Assignment" /><TableHeaderCell label="Account" /><TableHeaderCell label="Confirmed model / effort" /><TableHeaderCell label="Task state" /><TableHeaderCell label="Actions" />{/snippet}
      {#snippet children()}
        {#each visible as slot, index (slot.task_id ?? `${page}-${index}`)}
          <tr data-testid="queue-row">
            <td><div class="queue-assignment"><strong>{display(slot.task_summary, "Assignment unknown")}</strong><small class="mono">{display(slot.task_id)}</small></div></td>
            <td>{display(slot.account_id)}</td>
            <td><div>{display(slot.confirmed_model)}<small class="table-subline">{display(slot.confirmed_effort)} confirmed</small></div></td>
            <td><span class="queue-state"><i class="state-mark"></i>{display(slot.task_state)}</span><small class="table-subline">Observed {formatTimestamp(slot.observed_at)}</small></td>
            <td><div class="queue-actions"><Button size="sm" ariaLabel={`Inspect ${display(slot.task_summary, slot.task_id ?? "worker")}`} onclick={() => slot.task_id && oninspect(slot.task_id)} disabled={!slot.task_id}>Inspect</Button><button type="button" class="unsupported-action" disabled title={actionReason} aria-label="Resume">Resume</button></div></td>
          </tr>
        {/each}
      {/snippet}
    </Table>
    <div class="mobile-assignment-list">
      {#each visible as slot (slot.task_id ?? `mobile-${page}`)}
        <article class="mobile-assignment-card">
          <strong>{display(slot.task_summary, "Assignment unknown")}</strong>
          <small class="mono">{display(slot.task_id)}</small>
          <div class="mobile-assignment-meta"><span>{display(slot.account_id)}</span><span>{display(slot.task_state)}</span></div>
          <div class="mobile-assignment-meta"><span>{display(slot.confirmed_model)} · {display(slot.confirmed_effort)}</span><span>Observed {formatTimestamp(slot.observed_at)}</span></div>
          <div class="queue-actions"><Button size="sm" ariaLabel={`Inspect ${display(slot.task_summary, slot.task_id ?? "worker")}`} onclick={() => slot.task_id && oninspect(slot.task_id)} disabled={!slot.task_id}>Inspect</Button><button type="button" class="unsupported-action" disabled title={actionReason} aria-label="Resume">Resume</button></div>
        </article>
      {/each}
    </div>
    {#if !visible.length}
      <div class="empty-table"><strong>{query || statusFilter !== "all" ? "No assignments match this view" : "No occupied assignments"}</strong><span>Completed, failed and cancelled work is shown in History.</span></div>
    {/if}
  </div>
  <div class="pagination">
    <span>Page {page + 1} of {pageCount}</span>
    <div><button type="button" class="page-button kit-control-states" onclick={() => changePage(page - 1)} disabled={page === 0} aria-label="Previous page"><ChevronLeftIcon size={15} aria-hidden="true" /></button><button type="button" class="page-button kit-control-states" onclick={() => changePage(page + 1)} disabled={page >= pageCount - 1} aria-label="Next page"><ChevronRightIcon size={15} aria-hidden="true" /></button></div>
  </div>
</section>
