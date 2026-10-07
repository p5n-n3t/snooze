import { render, screen } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";
import Queue from "./Queue.svelte";
import { makeSlot, makeState } from "../test/fixtures";

describe("Queue", () => {
  it("shows occupied rows only and disables unsupported resume with a reason", () => {
    render(Queue, {
      props: {
        dashboard: makeState({ slots: [makeSlot(), makeSlot({ task_id: "done-1", task_state: "completed" })] }),
        oninspect: () => undefined,
      },
    });

    expect(screen.getAllByTestId("queue-row")).toHaveLength(1);
    const resumeButtons = screen.getAllByRole("button", { name: "Resume" });
    expect(resumeButtons).toHaveLength(2);
    for (const resume of resumeButtons) {
      expect(resume).toBeDisabled();
      expect(resume).toHaveAttribute("title", expect.stringContaining("not supported"));
    }
  });
});
