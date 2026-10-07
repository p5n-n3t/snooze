<script lang="ts">
  import { onMount } from "svelte";
  import Shell from "./components/Shell.svelte";
  import Watch from "./components/Watch.svelte";
  import Queue from "./components/Queue.svelte";
  import Providers from "./components/Providers.svelte";
  import History from "./components/History.svelte";
  import Settings from "./components/Settings.svelte";
  import TaskDrawer from "./components/TaskDrawer.svelte";
  import { getDashboardState, getHistory, getTaskDetail, postLegacy } from "./lib/api";
  import { LiveQuery } from "./lib/liveQuery.svelte";
  import type { DashboardState, HistoryEntry, PageKey, Slot, TaskDetail } from "./lib/types";

  let dashboard = $state<DashboardState | null>(null);
  let page = $state<PageKey>("watch");
  let theme = $state<"dark" | "light">("dark");
  let loading = $state(true);
  let checking = $state(false);
  let saving = $state(false);
  let loadError = $state("");
  let notice = $state("");
  let historyEntries = $state<HistoryEntry[]>([]);
  let historyLoading = $state(false);
  let historyError = $state("");
  let historyLoaded = $state(false);
  let drawerOpen = $state(false);
  let drawerLoading = $state(false);
  let drawerError = $state("");
  let taskDetail = $state<TaskDetail | null>(null);
  let selectedTaskId = $state<string | null>(null);
  const query = new LiveQuery();

  const selectedSlot = $derived(dashboard?.slots.find((slot) => slot.task_id === selectedTaskId) ?? null);
  const connectionLabel = $derived(loadError ? "Stale · last state retained" : dashboard ? "Connected" : "Connecting");

  function applyTheme(next: "dark" | "light") {
    theme = next;
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("snooze-theme", next); } catch { /* Storage may be disabled in private contexts. */ }
  }

  function toggleTheme() { applyTheme(theme === "dark" ? "light" : "dark"); }

  async function refreshState() {
    const generation = query.begin(performance.now());
    const start = performance.now();
    const step = query.start("dashboard state", start);
    if (!dashboard) loading = true;
    try {
      const next = await getDashboardState();
      if (!query.isCurrent(generation)) return;
      dashboard = next;
      loadError = "";
      query.settle(step, { name: "dashboard state", startMs: 0, durationMs: performance.now() - start });
    } catch (error) {
      if (!query.isCurrent(generation)) return;
      const message = error instanceof Error ? error.message : "The state request failed.";
      loadError = dashboard ? message : `Snooze could not load the worker state. ${message}`;
      query.abandon(step);
    } finally {
      query.end(generation);
      if (query.isCurrent(generation)) loading = false;
    }
  }

  async function refreshHistory() {
    historyLoading = true;
    try {
      historyEntries = await getHistory();
      historyError = "";
      historyLoaded = true;
    } catch (error) {
      historyError = error instanceof Error ? error.message : "The history request failed.";
    } finally {
      historyLoading = false;
    }
  }

  function navigate(next: PageKey) {
    page = next;
    window.scrollTo(0, 0);
    if (next === "history" && !historyLoaded) void refreshHistory();
  }

  async function inspect(taskId: string) {
    selectedTaskId = taskId;
    taskDetail = null;
    drawerError = "";
    drawerLoading = true;
    drawerOpen = true;
    try {
      taskDetail = await getTaskDetail(taskId);
    } catch (error) {
      drawerError = error instanceof Error ? error.message : "The task request failed.";
    } finally {
      drawerLoading = false;
    }
  }

  function closeDrawer() {
    drawerOpen = false;
    selectedTaskId = null;
    taskDetail = null;
    drawerError = "";
  }

  async function checkNow() {
    checking = true;
    notice = "";
    try {
      await postLegacy("/api/check", {});
      notice = "Check accepted by the local service. Watch will update when the next cycle is reported.";
      await refreshState();
    } catch (error) {
      notice = error instanceof Error ? error.message : "The check request failed.";
    } finally {
      checking = false;
    }
  }

  async function acknowledge(taskId: string | null, kind: string | null) {
    if (!taskId || !kind) return;
    notice = "";
    try {
      await postLegacy("/api/ack", { job: taskId, kind });
      notice = "Acknowledgement recorded by the local service.";
      await refreshState();
      if (historyLoaded) await refreshHistory();
    } catch (error) {
      notice = error instanceof Error ? error.message : "The acknowledgement was not recorded.";
    }
  }

  async function saveInterval(interval: number) {
    saving = true;
    notice = "";
    try {
      await postLegacy("/api/settings", { interval });
      notice = "Check interval saved by the local service.";
      await refreshState();
    } catch (error) {
      notice = error instanceof Error ? error.message : "The setting was not saved.";
    } finally {
      saving = false;
    }
  }

  onMount(() => {
    try {
      const saved = localStorage.getItem("snooze-theme");
      if (saved === "dark" || saved === "light") applyTheme(saved);
      else applyTheme("dark");
    } catch { applyTheme("dark"); }
    void refreshState();
    const timer = window.setInterval(() => void refreshState(), 10_000);
    return () => window.clearInterval(timer);
  });
</script>

<Shell active={page} projectName={dashboard?.project.name ?? "Snooze project"} {connectionLabel} {theme} onnav={navigate} ontoggleTheme={toggleTheme}>
  {#if dashboard}
    {#if loadError}<p class="stale-banner global-stale" role="status">Refresh failed: {loadError}. The last received state is still shown.</p>{/if}
    {#if page === "watch"}
      <Watch {dashboard} loading={checking} {notice} oninspect={inspect} oncheck={checkNow} onack={acknowledge} />
    {:else if page === "queue"}
      <Queue {dashboard} oninspect={inspect} />
    {:else if page === "providers"}
      <Providers {dashboard} />
    {:else if page === "history"}
      <History entries={historyEntries} loading={historyLoading} error={historyError} oninspect={inspect} />
    {:else}
      <Settings {dashboard} {saving} {notice} onsave={saveInterval} />
    {/if}
  {:else}
    <section class="startup-state" role="status"><div class="startup-mark">S</div><p class="eyebrow">LOCAL WORKER CONTROL</p><h1>Connecting to Snooze</h1><p>{loadError || "Loading the latest worker state…"}</p><button type="button" class="retry-button" onclick={() => void refreshState()}>Try again</button></section>
  {/if}
</Shell>

<TaskDrawer open={drawerOpen} detail={taskDetail} slot={selectedSlot} loading={drawerLoading} error={drawerError} onclose={closeDrawer} />
