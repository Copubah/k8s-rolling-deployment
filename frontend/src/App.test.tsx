import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import App from "./App";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
test("starts empty and records real successful responses", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          version: "v2",
          hostname: "pod-abc",
          timestamp: "2026-01-01T00:00:00Z",
          status: "ready",
        }),
      }),
  );
  render(<App />);
  expect(screen.getByText("0 total API requests")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Start traffic" }));
  await waitFor(() =>
    expect(screen.getByText("1 total API requests")).toBeInTheDocument(),
  );
  expect(screen.getAllByText("pod-abc").length).toBeGreaterThan(0);
  fireEvent.click(screen.getByRole("button", { name: "Stop traffic" }));
});
test("counts network failures without inventing a version", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "Start traffic" }));
  await waitFor(() => expect(screen.getByText("● Failed")).toBeInTheDocument());
  expect(screen.getByText("0 VERSIONS SEEN")).toBeInTheDocument();
});
