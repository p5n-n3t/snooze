<script lang="ts">
  import SettingsLayout from "../lib/kit/components/SettingsLayout.svelte";
  import Button from "../lib/kit/components/Button.svelte";
  import type { DashboardState } from "../lib/types";

  interface Props { dashboard: DashboardState; saving: boolean; notice: string; onsave: (interval: number) => void }
  let { dashboard, saving, notice, onsave }: Props = $props();
  const categories = [
    { id: "monitoring", label: "Monitoring", group: "Service", summary: "Check cadence and freshness" },
    { id: "dispatcher", label: "Dispatcher", group: "Service", summary: "Ownership and safety" },
    { id: "appearance", label: "Appearance", group: "Workspace", summary: "Theme and motion" },
  ];
  let active = $state("monitoring");
  let interval = $state("");
  $effect(() => { const currentInterval = dashboard.settings.interval; if (!saving) interval = String(currentInterval ?? 300); });
  const parsedInterval = $derived(Number(interval));
  const intervalValid = $derived(Number.isInteger(parsedInterval) && parsedInterval >= 30 && parsedInterval <= 86400);
</script>

<section class="page-view settings-view" data-testid="settings-view" aria-labelledby="settings-title">
  <div class="page-heading"><div><p class="eyebrow">SERVICE PREFERENCES / LOCAL ONLY</p><h1 id="settings-title">Settings<span class="heading-period">.</span></h1><p class="page-subtitle">Keep the observation service predictable and its controls honest.</p></div></div>
  {#if notice}<p class="inline-notice" role="status">{notice}</p>{/if}
  <div class="settings-frame">
    <SettingsLayout {categories} bind:active title="Settings">
      {#snippet panel(category)}
        {#if category === "monitoring"}
          <div class="settings-panel-heading"><p class="eyebrow">SERVICE / MONITORING</p><h2>Check cadence</h2><p>Choose how often Snooze checks the configured worker sources. Monitoring cadence does not change worker-slot capacity.</p></div>
          <div class="settings-group"><div><label for="check-interval">Check interval</label><p>Minimum 30 seconds. The next check time is reported only when the service confirms it.</p></div><div class="interval-control"><input id="check-interval" type="number" min="30" max="86400" step="1" bind:value={interval} /><span>seconds</span><Button tone="info" surface="solid" disabled={!intervalValid || saving} onclick={() => onsave(parsedInterval)}>{saving ? "Saving…" : "Save interval"}</Button></div></div>
          {#if !intervalValid}<p class="field-error" role="alert">Enter a whole number from 30 to 86,400 seconds.</p>{/if}
          <div class="settings-group settings-readonly"><div><strong>Last completed check</strong><p>The value shown in Watch comes from the actual check cycle.</p></div><span>{dashboard.cycle.checked ? new Date(dashboard.cycle.checked * 1000).toLocaleString() : "Not reported"}</span></div>
        {:else if category === "dispatcher"}
          <div class="settings-panel-heading"><p class="eyebrow">SERVICE / OWNERSHIP</p><h2>Dispatcher safety</h2><p>Snooze observes worker state here. It does not own the configured executor.</p></div>
          <div class="ownership-callout"><span class="ownership-icon">!</span><div><strong>Dispatcher controls are unavailable</strong><p>{dashboard.capabilities.dispatch.reason || "Dispatch is not enabled."} A local pause flag cannot pause an external worker.</p></div></div>
          <div class="settings-disabled-controls"><button type="button" disabled title={dashboard.capabilities.dispatch.reason}>Pause dispatch</button><button type="button" disabled title={dashboard.capabilities.dispatch.reason}>Emergency stop</button></div>
        {:else}
          <div class="settings-panel-heading"><p class="eyebrow">WORKSPACE / APPEARANCE</p><h2>Reading comfort</h2><p>Use the theme control in the top bar. OS reduced-motion preferences are respected throughout the interface.</p></div>
          <div class="settings-group settings-readonly"><div><strong>Motion</strong><p>Drawer transitions and activity indicators follow your system preference.</p></div><span>System preference</span></div>
        {/if}
      {/snippet}
    </SettingsLayout>
  </div>
</section>
