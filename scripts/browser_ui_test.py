#!/usr/bin/env python3
"""Browser-level UI tests for the DroneOps control station."""

import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import expect, sync_playwright  # noqa: E402

from control_station.http_server import ControlStationHandler, ControlStationServer  # noqa: E402
from control_station.mission_session import ControlStationMissionSession  # noqa: E402


def start_server():
    session = ControlStationMissionSession()
    server = ControlStationServer(("127.0.0.1", 0), ControlStationHandler, session, "")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, "http://{}:{}".format(host, port)


def click_first_fallback_drone(page):
    page.wait_for_function("() => state.fallbackDroneHits && state.fallbackDroneHits.length > 0")
    hit = page.evaluate("() => state.fallbackDroneHits[0]")
    box = page.locator("#fallbackMap").bounding_box()
    size = page.evaluate("() => ({ width: document.getElementById('fallbackMap').width, height: document.getElementById('fallbackMap').height })")
    click_x = box["x"] + (hit["x"] / size["width"]) * box["width"]
    click_y = box["y"] + (hit["y"] / size["height"]) * box["height"]
    page.mouse.click(click_x, click_y)
    return hit


def hover_first_fallback_drone(page):
    page.wait_for_function("() => state.fallbackDroneHits && state.fallbackDroneHits.length > 0")
    hit = page.evaluate("() => state.fallbackDroneHits[0]")
    box = page.locator("#fallbackMap").bounding_box()
    size = page.evaluate("() => ({ width: document.getElementById('fallbackMap').width, height: document.getElementById('fallbackMap').height })")
    hover_x = box["x"] + (hit["x"] / size["width"]) * box["width"]
    hover_y = box["y"] + (hit["y"] / size["height"]) * box["height"]
    page.mouse.move(hover_x, hover_y)
    return hit


def run_browser_checks(url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 850})
        page.goto(url, wait_until="domcontentloaded")

        assert page.locator("#droneModal").evaluate("el => !el.classList.contains('open')")
        expect(page.locator("#holdBtn")).to_be_disabled()
        expect(page.locator("#resumeBtn")).to_be_disabled()
        expect(page.locator("#returnBtn")).to_be_disabled()
        expect(page.locator("#liveOrderHint")).to_contain_text("Start a mission")
        expect(page.locator("#phaseText")).to_contain_text("Plan a route")
        expect(page.locator("#assets .row")).to_have_count(3, timeout=5000)

        page.locator("#startBtn").click()
        expect(page.locator("#drones .row")).to_have_count(4, timeout=5000)
        expect(page.locator("#holdBtn")).to_be_enabled()
        expect(page.locator("#phaseText")).to_contain_text("Route")
        page.evaluate("""async () => {
            await fetch('/api/observations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    reportId: 'obs.browser.red-roof',
                    reportingNodeId: 'drone-01',
                    label: 'Red roof',
                    category: 'structure_feature',
                    confidence: 0.88,
                    position: { lat: 44.4081, lon: 26.3142, alt: 88 },
                    imageDataUri: 'data:image/svg+xml;utf8,%3Csvg%3E%3C/svg%3E'
                })
            });
        }""")
        page.wait_for_function("() => document.querySelectorAll('#observations .observationRow').length > 0")
        expect(page.locator("#observations")).to_contain_text("Red roof")
        page.locator("#observations .observationRow").first.click()
        page.wait_for_function("() => document.getElementById('observationTooltip').classList.contains('open')")
        expect(page.locator("#observationDetails")).to_contain_text("Reporting drone")
        page.locator("#closeObservationBtn").click()

        page.locator("#drones .row").first.click(timeout=1000)
        assert page.locator("#droneModal").evaluate("el => !el.classList.contains('open')")

        hover_hit = hover_first_fallback_drone(page)
        page.wait_for_function("() => document.getElementById('droneModal').classList.contains('open')")
        expect(page.locator("#modalTitle")).to_contain_text(hover_hit["nodeId"])
        follow_after_hover = page.evaluate("() => state.followDroneId")
        assert follow_after_hover is None, "hover should not pin follow mode"

        page.locator("#closeModalBtn").click()
        page.wait_for_function("() => !document.getElementById('droneModal').classList.contains('open')")

        click_hit = click_first_fallback_drone(page)
        page.wait_for_function("() => document.getElementById('droneModal').classList.contains('open')")
        expect(page.locator("#modalTitle")).to_contain_text(click_hit["nodeId"])
        page.wait_for_function("(nodeId) => state.followDroneId === nodeId", arg=click_hit["nodeId"])
        expect(page.locator("#modalStatus")).to_contain_text("Pinned")

        before = page.locator("#paramGrid").inner_text()
        before_box = page.locator("#droneModal").bounding_box()
        page.wait_for_timeout(1400)
        after = page.locator("#paramGrid").inner_text()
        after_box = page.locator("#droneModal").bounding_box()
        assert before != after, "followed drone telemetry should refresh while modal is open"
        assert before_box != after_box, "pinned telemetry tooltip should move with the drone"

        page.locator("#unfollowBtn").click()
        page.wait_for_function("() => state.followDroneId === null")
        expect(page.locator("#modalStatus")).not_to_contain_text("Pinned")
        browser.close()


def main():
    server, url = start_server()
    try:
        run_browser_checks(url)
        print("Browser UI checks passed.")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
