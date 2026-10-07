import { fireEvent, render, screen } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";
import History from "./History.svelte";
import { makeHistory } from "../test/fixtures";

describe("History", () => {
  it("bounds rendered rows and pages through a large history set", async () => {
    render(History, { props: { entries: makeHistory(10_000), loading: false, error: "" } });

    expect(screen.getAllByTestId("history-row")).toHaveLength(25);
    expect(screen.getByText("Showing 1–25 of 10,000 records")).toBeInTheDocument();
    await fireEvent.click(screen.getByRole("button", { name: "Next page" }));
    expect(screen.getByText("Recorded outcome 25")).toBeInTheDocument();
    expect(screen.getAllByTestId("history-row")).toHaveLength(25);
  });
});
