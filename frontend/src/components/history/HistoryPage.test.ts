import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getEngineReport, getHistoryReport } from "../../lib/history-api";
import HistoryPage from "./HistoryPage.svelte";
import { makeHistoryResponse } from "./history-fixtures";

vi.mock("../../lib/history-api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../lib/history-api")>();
  return { ...actual, getHistoryReport: vi.fn(), getEngineReport: vi.fn() };
});

const mockedHistory = vi.mocked(getHistoryReport);
const mockedEngine = vi.mocked(getEngineReport);

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

describe("HistoryPage", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", "/history?from_utc=2026-10-01T00%3A00%3A00.000Z&to_utc=2026-10-08T00%3A00%3A00.000Z&timezone=UTC");
    window.localStorage.clear();
    mockedHistory.mockReset();
    mockedEngine.mockReset();
    mockedHistory.mockResolvedValue(makeHistoryResponse());
    mockedEngine.mockResolvedValue({ state: "unavailable", payload: {}, source_version: null, source_window: null, coverage: { state: "unavailable" }, error_kind: "not_configured" });
  });
  afterEach(() => cleanup());

  it("renders real zero separately from unavailable metrics and exposes current project exports", async () => {
    render(HistoryPage);
    await screen.findByText("current-snooze");
    const zeroMetric = screen.getByText("Recorded events").closest("article");
    expect(zeroMetric && within(zeroMetric).getByText("4")).toBeTruthy();
    const retries = screen.getByText("Retry rate").closest("article");
    expect(retries && within(retries).getByText("0%")).toBeTruthy();
    const input = screen.getByText("Input tokens").closest("article");
    expect(input && within(input).getByText("Unavailable")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Export CSV" }).getAttribute("href")).toContain("/api/v2/history/export?");
    expect(screen.getByRole("link", { name: "Export JSON" }).getAttribute("href")).toContain("format=json");
  });

  it("keeps observed and estimated currencies labeled separately and shows provenance", async () => {
    render(HistoryPage);
    await screen.findByText("current-snooze");
    expect(screen.getByRole("heading", { name: "Provider reported" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Estimated" })).toBeTruthy();
    expect(screen.getAllByText("1.25 USD")).toHaveLength(2);
    expect(screen.getByText("1.5 EUR")).toBeTruthy();
    expect(screen.getByText("2.1 USD")).toBeTruthy();
    expect(screen.getByText("provider_reported")).toBeTruthy();
    expect(screen.getByText("2.4.1+abc123 (API 1)")).toBeTruthy();
  });

  it("loads the optional external engine report only when requested and keeps it unavailable", async () => {
    render(HistoryPage);
    await screen.findByText("current-snooze");
    expect(mockedEngine).not.toHaveBeenCalled();
    await fireEvent.click(screen.getByRole("button", { name: "Load external report" }));
    await screen.findByText("No provider analytics service is configured.");
    expect(mockedEngine).toHaveBeenCalledTimes(1);
    expect(mockedEngine.mock.calls[0]?.[0]).toBe("usage_summary");
    expect(screen.getByText(/Snooze-native totals above are unchanged/)).toBeTruthy();
  });

  it("coalesces rapid filter edits into one bounded report request", async () => {
    render(HistoryPage);
    await screen.findByText("current-snooze");
    await fireEvent.change(screen.getByLabelText("To"), { target: { value: "2026-10-09" } });
    await fireEvent.change(screen.getByLabelText("To"), { target: { value: "2026-10-10" } });
    await waitFor(() => expect(mockedHistory).toHaveBeenCalledTimes(2), { timeout: 1500 });
    await new Promise((resolve) => setTimeout(resolve, 350));
    expect(mockedHistory).toHaveBeenCalledTimes(2);
    expect(mockedHistory.mock.calls[1]?.[0].toUtc).toBe("2026-10-11T00:00:00.000Z");
  });

  it("keeps a stale response visible while filters refresh and ignores a late cancelled result", async () => {
    const cancelledResponse = deferred<ReturnType<typeof makeHistoryResponse>>();
    const currentResponse = deferred<ReturnType<typeof makeHistoryResponse>>();
    mockedHistory.mockReset().mockResolvedValueOnce(makeHistoryResponse({ events: 4 })).mockReturnValueOnce(cancelledResponse.promise).mockReturnValueOnce(currentResponse.promise);
    const inspected = vi.fn();
    render(HistoryPage, { props: { oninspect: inspected } });
    await waitFor(() => expect(mockedHistory).toHaveBeenCalledTimes(1));
    await screen.findByText("current-snooze");

    await fireEvent.change(screen.getByLabelText("To"), { target: { value: "2026-10-10" } });
    expect(screen.getByText(/Filters changed/)).toBeTruthy();
    await waitFor(() => expect(mockedHistory).toHaveBeenCalledTimes(2), { timeout: 1500 });
    await fireEvent.change(screen.getByLabelText("To"), { target: { value: "2026-10-11" } });
    await waitFor(() => expect(mockedHistory).toHaveBeenCalledTimes(3), { timeout: 1500 });
    currentResponse.resolve(makeHistoryResponse({ events: 21 }));
    const eventCard = screen.getByText("Recorded events").closest("article");
    await waitFor(() => expect(eventCard && within(eventCard).getByText("21")).toBeTruthy());

    cancelledResponse.resolve(makeHistoryResponse({ events: 99 }));
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(eventCard && within(eventCard).queryByText("99")).toBeNull();
    expect(inspected).not.toHaveBeenCalled();
    expect(screen.queryByRole("button", { name: "Inspect task" })).toBeNull();
  });
});
