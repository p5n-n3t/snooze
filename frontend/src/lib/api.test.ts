import { describe, expect, it, vi } from "vitest";
import { getHistory, postControl } from "./api";

describe("future control client", () => {
  it("returns the backend receipt without treating submission as success", async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: "pending", message: "Waiting for the worker owner." }),
    });

    const receipt = await postControl(
      { action: "resume", target_id: "task-1", values: {}, expected_revision: 8 },
      fetcher,
    );

    expect(fetcher).toHaveBeenCalledWith(
      "/api/v2/control",
      expect.objectContaining({ method: "POST", credentials: "same-origin" }),
    );
    expect(receipt.status).toBe("pending");
    expect(receipt.message).toMatch(/Waiting for the worker owner/);
  });
});

describe("legacy history boundary", () => {
  it("moves completed sessions into normalized history without inventing detail", async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        workers: [
          { id: "done-1", title: "Finished run", state: "completed", observed_at: 42 },
          { id: "running-1", title: "Live run", state: "running", observed_at: 43 },
        ],
        incidents: [],
      }),
    });

    const history = await getHistory(fetcher);
    expect(history).toHaveLength(1);
    expect(history[0]).toMatchObject({ id: "task:done-1", kind: "completed", title: "Finished run", at: 42 });
    expect(history[0].detail).toContain("unavailable");
  });
});
