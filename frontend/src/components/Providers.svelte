<script lang="ts">
  import Building2Icon from "@lucide/svelte/icons/building-2";
  import CircleHelpIcon from "@lucide/svelte/icons/circle-help";
  import ShieldCheckIcon from "@lucide/svelte/icons/shield-check";
  import TextInput from "../lib/kit/components/TextInput.svelte";
  import type { DashboardState } from "../lib/types";

  interface Props { dashboard: DashboardState }
  let { dashboard }: Props = $props();
  const providerReason = "Provider configuration is owned by the local runtime and is not writable through this dashboard yet.";
</script>

<section class="page-view providers-view" data-testid="providers-view" aria-labelledby="providers-title">
  <div class="page-heading">
    <div><p class="eyebrow">CONNECTED WORKERS / ACCOUNT MAP</p><h1 id="providers-title">Providers<span class="heading-period">.</span></h1><p class="page-subtitle">Account labels and capacity as reported by the local Snooze configuration.</p></div>
    <div class="provider-summary"><ShieldCheckIcon size={16} aria-hidden="true" /><span>Credentials stay on the local service</span></div>
  </div>
  <div class="provider-notice"><CircleHelpIcon size={16} aria-hidden="true" /><p>Secret values are not read or echoed here. Provider connections and identity checks remain controlled by the configured runtime.</p></div>
  {#if dashboard.accounts.length}
    <div class="provider-list">
      {#each dashboard.accounts as account, index (`${account.server_key}-${index}`)}
        <article class="provider-card">
          <div class="provider-card-heading"><span class="provider-glyph"><Building2Icon size={18} aria-hidden="true" /></span><div><span class="eyebrow">ACCOUNT {String(index + 1).padStart(2, "0")}</span><h2>{account.label ?? account.server_key ?? "Unlabelled account"}</h2><p class="mono">{account.server_key ?? "Identity not reported"}</p></div><span class:account-enabled={account.enabled} class:account-disabled={account.enabled === false} class="provider-enabled">{account.enabled === false ? "Disabled" : account.enabled === true ? "Enabled" : "State unknown"}</span></div>
          <div class="provider-fields">
            <label>Display label<TextInput value={account.label ?? account.server_key ?? ""} ariaLabel={`Display label for account ${account.server_key ?? index + 1}`} /></label>
            <label>Configured capacity<div class="capacity-field"><input type="number" min="0" value={account.capacity ?? ""} aria-label={`Configured capacity for ${account.label ?? account.server_key ?? index + 1}`} readonly /><span>worker slots</span></div></label>
            <div class="provider-field"><span class="provider-field-label">Credential status</span><div class="credential-state"><span class="credential-dot"></span>Stored by local runtime</div></div>
          </div>
          <div class="provider-card-footer"><span>Fields are ready for the provider configuration API.</span><div><button type="button" class="provider-disabled" disabled title={providerReason}>Test connection</button><button type="button" class="provider-disabled" disabled title={providerReason}>Save account</button></div></div>
        </article>
      {/each}
    </div>
  {:else}
    <div class="quiet-state"><span class="quiet-mark">⌁</span><div><strong>No configured provider accounts</strong><p>The service did not report any account labels or capacity.</p></div></div>
  {/if}
</section>
