#!/usr/bin/env python3
"""Browser UI template for the simulation control station."""

import json


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>DroneOps Control Station</title>
  <style>
    :root { color-scheme: dark; font-family: Arial, Helvetica, sans-serif; background: #101417; color: #eef4f8; }
    body { margin: 0; height: 100vh; display: grid; grid-template-rows: auto 1fr; background: linear-gradient(135deg, #101417 0%, #151d20 42%, #0f1317 100%); }
    header { display: flex; justify-content: space-between; align-items: center; padding: 13px 16px; background: rgba(26, 32, 38, .96); border-bottom: 1px solid #303943; box-shadow: 0 10px 28px rgba(0,0,0,.24); }
    h1 { margin: 0; font-size: 18px; }
    main { min-height: 0; display: grid; grid-template-columns: 410px 1fr; }
    aside { overflow: auto; padding: 14px; background: rgba(23, 29, 34, .96); border-right: 1px solid #303943; }
    label { display: block; margin: 12px 0 6px; color: #b8c5cf; font-size: 13px; }
    textarea, input { box-sizing: border-box; width: 100%; border: 1px solid #3a4650; border-radius: 6px; padding: 8px; background: #0f1317; color: #f6fafc; font: inherit; outline: none; }
    textarea:focus, input:focus { border-color: #55a7d8; box-shadow: 0 0 0 2px rgba(85,167,216,.16); }
    textarea { min-height: 86px; resize: vertical; }
    button { width: 100%; margin-top: 10px; border: 0; border-radius: 6px; padding: 9px 10px; background: #2e7d62; color: #fff; font-weight: 700; cursor: pointer; }
    button:disabled { opacity: .45; cursor: not-allowed; }
    button.secondary { background: #384655; }
    button.warning { background: #866337; }
    button.danger { background: #79383b; }
    button.small { width: auto; margin: 0; padding: 7px 8px; font-size: 12px; }
    .badge { color: #9bd4ff; font-size: 12px; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
    .panel { margin-top: 14px; padding: 12px; border: 1px solid #2d3740; border-radius: 8px; background: rgba(17, 23, 28, .92); box-shadow: inset 0 1px 0 rgba(255,255,255,.03); }
    .panelTitle { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 13px; font-weight: 700; }
    .micro { color: #9eacb7; font-size: 12px; line-height: 1.35; }
    .status { margin-top: 12px; padding: 10px; border-radius: 6px; background: #222b33; color: #dce6ee; font-size: 13px; line-height: 1.35; }
    .phasePanel { margin-top: 12px; padding: 10px; border: 1px solid #303943; border-radius: 8px; background: #121920; }
    .phaseTrack { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
    .phaseStep { padding: 7px 6px; border: 1px solid #303943; border-radius: 6px; color: #8795a1; background: #10151a; font-size: 11px; text-align: center; }
    .phaseStep.active { border-color: #55a7d8; color: #eef4f8; background: #173040; }
    .phaseStep.done { border-color: #2e7d62; color: #dff8eb; background: #13251d; }
    .progressShell { height: 6px; margin-top: 8px; overflow: hidden; border-radius: 999px; background: #26313a; }
    .progressFill { width: 0%; height: 100%; background: #55a7d8; transition: width .2s ease; }
    .rows { display: grid; gap: 8px; margin-top: 10px; }
    .row, .droneCard { display: grid; grid-template-columns: 1fr auto; gap: 8px; padding: 8px; border: 1px solid #303943; border-radius: 6px; background: #151b20; font-size: 13px; cursor: pointer; transition: border-color .15s ease, background .15s ease, transform .15s ease; }
    .row:hover, .droneCard:hover { border-color: #587183; background: #18232a; }
    .droneCard { grid-template-columns: auto auto 1fr auto; align-items: center; }
    .droneCard.selected { border-color: var(--drone-color); background: #17251f; box-shadow: inset 3px 0 0 var(--drone-color); }
    .droneCard input { width: auto; }
    .droneGlyph { width: 24px; height: 24px; display: grid; place-items: center; background: var(--drone-color); color: #071015; font-size: 11px; font-weight: 800; box-shadow: 0 0 0 2px rgba(255,255,255,.08), 0 8px 18px rgba(0,0,0,.28); }
    .assetGlyph { width: 22px; height: 22px; display: inline-grid; place-items: center; margin-right: 8px; vertical-align: middle; border: 2px solid var(--asset-color); color: var(--asset-color); background: rgba(16,21,26,.92); font-size: 10px; font-weight: 800; }
    .asset-ground { border-radius: 4px; }
    .asset-air { clip-path: polygon(50% 0, 100% 100%, 50% 72%, 0 100%); border-radius: 0; background: var(--asset-color); color: #071015; }
    .observationRow { grid-template-columns: 64px 1fr; align-items: center; cursor: pointer; }
    .observationThumb { width: 58px; height: 42px; object-fit: cover; border: 1px solid #3a4650; border-radius: 5px; background: #0f1317; }
    .observationPin { width: 24px; height: 24px; display: inline-grid; place-items: center; margin-right: 8px; vertical-align: middle; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 2px solid #071015; background: #ff7a68; color: #071015; font-size: 12px; font-weight: 900; }
    .observationPin span { transform: rotate(45deg); }
    .shape-triangle { clip-path: polygon(50% 0, 100% 100%, 50% 72%, 0 100%); }
    .shape-diamond { clip-path: polygon(50% 0, 100% 50%, 50% 100%, 0 50%); }
    .shape-square { border-radius: 5px; }
    .shape-hex { clip-path: polygon(25% 4%, 75% 4%, 100% 50%, 75% 96%, 25% 96%, 0 50%); }
    .shape-circle { border-radius: 50%; }
    .shape-kite { clip-path: polygon(50% 0, 90% 42%, 58% 100%, 42% 100%, 10% 42%); }
    .waypointRow { display: grid; grid-template-columns: 18px 48px 1fr 1fr 68px 30px; gap: 6px; align-items: center; margin-top: 6px; }
    .waypointRow input { padding: 7px; font-size: 12px; }
    .waypointLabel { color: #cbd5dd; font-size: 11px; font-weight: 700; }
    .waypointSwatch { width: 14px; height: 14px; border-radius: 50%; background: var(--waypoint-color); box-shadow: 0 0 0 2px rgba(255,255,255,.12); }
    details.diagnostics { margin-top: 12px; border: 1px solid #303943; border-radius: 8px; background: #121920; }
    details.diagnostics summary { cursor: pointer; padding: 9px 10px; color: #cbd5dd; font-size: 13px; font-weight: 700; }
    details.diagnostics .status { margin: 0 10px 10px; }
    #mapShell { position: relative; min-height: 0; background: #090d10; }
    #map { position: absolute; inset: 0; }
    #fallbackMap { position: absolute; inset: 0; width: 100%; height: 100%; display: none; }
    .mapTools { position: absolute; z-index: 5; top: 12px; left: 12px; display: flex; gap: 8px; flex-wrap: wrap; }
    .modal { position: fixed; left: 0; top: 0; display: none; z-index: 20; pointer-events: none; transform: translate(14px, -50%); }
    .modal.open { display: block; }
    .modalPanel { width: min(310px, 90vw); max-height: min(430px, 82vh); display: grid; grid-template-rows: auto 1fr; border: 1px solid #3a4650; border-radius: 8px; background: #151b20; overflow: hidden; box-shadow: 0 16px 46px rgba(0,0,0,.4); pointer-events: auto; }
    .modalPanel::before { content: ""; position: absolute; left: -8px; top: calc(50% - 8px); width: 0; height: 0; border-top: 8px solid transparent; border-bottom: 8px solid transparent; border-right: 8px solid #3a4650; }
    .modalHead { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 7px 8px; border-bottom: 1px solid #303943; }
    .modalHead h2 { margin: 0; font-size: 13px; }
    .modalHead button { width: auto; margin: 0; padding: 6px 7px; font-size: 11px; }
    .modalActions { display: flex; gap: 6px; align-items: center; }
    .modalBody { display: grid; grid-template-rows: auto 125px; min-height: 0; }
    .observationPanel { width: min(300px, 88vw); }
    .observationBody { display: grid; gap: 8px; padding: 8px; }
    .observationImage { width: 100%; height: 130px; object-fit: cover; border: 1px solid #303943; border-radius: 6px; background: #0f1317; }
    .paramPanel { padding: 8px; overflow: auto; border-bottom: 1px solid #303943; }
    .param { display: grid; grid-template-columns: 76px 1fr; gap: 6px; padding: 4px 6px; margin-top: 4px; border: 1px solid #303943; border-radius: 6px; background: #10151a; font-size: 11px; }
    .param span:first-child { color: #9eacb7; }
    #streetView, #streetFallback { min-height: 125px; }
    #streetFallback { display: flex; align-items: center; justify-content: center; padding: 14px; color: #cbd5dd; text-align: center; font-size: 11px; }
    @media (max-width: 820px) { main { grid-template-columns: 1fr; grid-template-rows: auto 55vh; } aside { border-right: 0; border-bottom: 1px solid #303943; } .modalPanel { width: min(300px, 88vw); } }
  </style>
</head>
<body>
  <header><h1>DroneOps Control Station</h1><div class="badge">SIMULATION_ONLY</div></header>
  <main>
    <aside>
      <label for="order">Order</label>
      <textarea id="order">coordinate with peers and simulate the Bucharest outskirts route</textarea>
      <div class="grid2">
        <div><label for="nodes">Drones</label><input id="nodes" type="number" min="1" max="12" value="4"></div>
        <div><label for="ticks">Route duration</label><input id="ticks" type="number" min="2" max="300" value="36"></div>
      </div>
      <div class="phasePanel">
        <div class="phaseTrack">
          <div id="phaseIdle" class="phaseStep active">Plan</div>
          <div id="phaseRoute" class="phaseStep">Route</div>
          <div id="phaseReturn" class="phaseStep">RTH</div>
          <div id="phaseComplete" class="phaseStep">Complete</div>
        </div>
        <div class="progressShell"><div id="phaseProgress" class="progressFill"></div></div>
        <div id="phaseText" class="micro">Plan a route and start the simulation.</div>
      </div>
      <div class="panel">
        <div class="panelTitle"><span>Mission Fleet / Live Targets</span><span><button id="selectAllBtn" class="secondary small">All</button> <button id="selectNoneBtn" class="secondary small">None</button></span></div>
        <div class="micro">Before start, these drones join the mission. During a run, the same selection receives live orders.</div>
        <div id="fleetRoster" class="rows"></div>
      </div>
      <div class="panel">
        <div class="panelTitle"><span>Mission Waypoints</span><button id="resetRouteBtn" class="secondary small">Reset</button></div>
        <div class="micro">Click the map while drawing is on, or edit waypoint values directly.</div>
        <div id="waypoints"></div>
        <div class="grid3"><button id="addWaypointBtn" class="secondary">Add Waypoint</button><button id="clearRouteBtn" class="danger">Clear</button><button id="undoClearBtn" class="secondary" style="display:none;">Undo</button></div>
      </div>
      <button id="startBtn">Start Simulation</button>
      <div class="panel">
        <div class="panelTitle"><span>Simulated Live Orders</span></div>
        <div id="liveOrderHint" class="micro">Start a mission to enable live orders.</div>
        <div class="grid3"><button id="holdBtn" class="warning">Hold</button><button id="resumeBtn" class="secondary">Resume</button><button id="returnBtn" class="danger">Return Home</button></div>
      </div>
      <div id="status" class="status">Ready.</div>
      <label>Tracked Drones</label><div id="drones" class="rows"></div>
      <label>Observation Reports</label><div id="observations" class="rows"></div>
      <label>External Assets <span class="micro">(read-only)</span></label><div id="assets" class="rows"></div>
      <details class="diagnostics">
        <summary>Diagnostics</summary>
        <label>Network Topics</label><div id="topics" class="status">none</div>
      </details>
    </aside>
    <section id="mapShell">
      <div class="mapTools"><button id="drawModeBtn" class="secondary small">Drawing On</button></div>
      <div id="map"></div><canvas id="fallbackMap"></canvas>
    </section>
  </main>
  <div id="droneModal" class="modal" aria-hidden="true">
    <div class="modalPanel">
      <div class="modalHead"><h2 id="modalTitle">Drone</h2><div class="modalActions"><button id="unfollowBtn" class="secondary">Unfollow</button><button id="closeModalBtn" class="secondary">Close</button></div></div>
      <div class="modalBody"><section class="paramPanel"><div id="modalStatus" class="status">Simulated onboard parameters</div><div id="paramGrid"></div></section><section><div id="streetView"></div><div id="streetFallback">Street View imagery will appear here when available.</div></section></div>
    </div>
  </div>
  <div id="observationTooltip" class="modal" aria-hidden="true">
    <div class="modalPanel observationPanel">
      <div class="modalHead"><h2 id="observationTitle">Observation</h2><button id="closeObservationBtn" class="secondary">Close</button></div>
      <div class="observationBody">
        <img id="observationImage" class="observationImage" alt="Observation capture">
        <div id="observationDetails" class="status">No observation selected.</div>
      </div>
    </div>
  </div>
  <script>
    window.DRONEOPS_CONFIG = __CONFIG__;
    const state = {
      map: null, googleReady: false, streetService: null, streetPanorama: null,
      route: window.DRONEOPS_CONFIG.defaultRoute.map(p => ({ ...p })),
      selectedNodeIds: new Set(['drone-01', 'drone-02', 'drone-03', 'drone-04']),
      availableDrones: [],
      latestDrones: {}, latestAssets: {}, latestObservations: {}, droneMarkers: {}, assetMarkers: {}, observationMarkers: {}, routeMarkers: [], routeLines: [],
      drawMode: true, selectedDroneId: null, followDroneId: null, knownExecuting: new Set(),
      streetLast: { nodeId: null, lat: null, lon: null, at: 0 },
      fallbackDroneHits: [], fallbackObservationHits: [],
      fallbackProjection: null,
      missionStatus: 'idle',
      requestBusy: false,
      tooltipAnchor: null,
      observationAnchor: null,
      selectedObservationId: null,
      lastRouteBeforeClear: null
    };
    const $ = id => document.getElementById(id);
    function escapeHtml(value) { return String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch])); }
    const dronePalette = [
      { color: '#47c2ff', shape: 'triangle', path: 'M 0 -13 L 11 11 L 0 6 L -11 11 Z' },
      { color: '#f5b84b', shape: 'diamond', path: 'M 0 -12 L 12 0 L 0 12 L -12 0 Z' },
      { color: '#7ee081', shape: 'square', path: 'M -10 -10 L 10 -10 L 10 10 L -10 10 Z' },
      { color: '#d88cff', shape: 'hex', path: 'M 0 -12 L 10 -6 L 10 6 L 0 12 L -10 6 L -10 -6 Z' },
      { color: '#ff7a68', shape: 'circle', path: 'M 0 -12 L 8 -8 L 12 0 L 8 8 L 0 12 L -8 8 L -12 0 L -8 -8 Z' },
      { color: '#74d6c1', shape: 'kite', path: 'M 0 -13 L 10 -2 L 4 12 L -4 12 L -10 -2 Z' },
      { color: '#b9d36a', shape: 'triangle', path: 'M 0 -13 L 11 11 L 0 6 L -11 11 Z' },
      { color: '#ff9fc1', shape: 'diamond', path: 'M 0 -12 L 12 0 L 0 12 L -12 0 Z' },
      { color: '#8fb7ff', shape: 'square', path: 'M -10 -10 L 10 -10 L 10 10 L -10 10 Z' },
      { color: '#f08f4f', shape: 'hex', path: 'M 0 -12 L 10 -6 L 10 6 L 0 12 L -10 6 L -10 -6 Z' },
      { color: '#63e6a7', shape: 'circle', path: 'M 0 -12 L 8 -8 L 12 0 L 8 8 L 0 12 L -8 8 L -12 0 L -8 -8 Z' },
      { color: '#c5a6ff', shape: 'kite', path: 'M 0 -13 L 10 -2 L 4 12 L -4 12 L -10 -2 Z' }
    ];
    const waypointPalette = ['#41d68b', '#55a7ff', '#f5b84b', '#d88cff', '#ff7a68', '#74d6c1'];
    function setStatus(text) { $('status').textContent = text; }
    function missionIsActive() { return state.missionStatus === 'running' && Object.keys(state.latestDrones).length > 0; }
    function updateActionStates() {
      const canStart = state.route.length >= 2 && state.selectedNodeIds.size > 0;
      $('startBtn').disabled = !canStart || state.requestBusy;
      const executingSelected = [...state.selectedNodeIds].some(id => state.latestDrones[id]);
      const canOrder = missionIsActive() && executingSelected && !state.requestBusy;
      $('holdBtn').disabled = !canOrder;
      $('resumeBtn').disabled = !canOrder;
      $('returnBtn').disabled = !canOrder;
      $('liveOrderHint').textContent = canOrder ? 'Live orders target selected drones in this simulation only.' : 'Start a mission and select an executing drone to enable live orders.';
    }
    function generatedFleetIds() { const count = Math.max(1, Math.min(12, Number($('nodes').value || 4))); return Array.from({ length: count }, (_, i) => `drone-${String(i + 1).padStart(2, '0')}`); }
    function fleetIds() {
      const ids = [...generatedFleetIds()];
      for (const drone of state.availableDrones) if (!ids.includes(drone.nodeId)) ids.push(drone.nodeId);
      return ids;
    }
    function fleetInfo(nodeId) { return state.availableDrones.find(drone => drone.nodeId === nodeId) || {}; }
    function droneNumber(nodeId) {
      const numeric = Number(String(nodeId).match(/(\d+)$/)?.[1]);
      if (Number.isFinite(numeric) && numeric > 0) return numeric;
      return Math.max(1, fleetIds().indexOf(nodeId) + 1);
    }
    function droneIdentity(nodeId) { return dronePalette[(droneNumber(nodeId) - 1) % dronePalette.length]; }
    function droneBadge(nodeId) {
      const match = String(nodeId).match(/drone-(\d+)$/);
      if (match) return `D${Number(match[1])}`;
      return String(nodeId).split(/[-_]/).filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase().slice(0, 2) || 'D';
    }
    function waypointColor(index, total) {
      if (index === 0) return '#41d68b';
      if (index === total - 1) return '#ff7a68';
      return waypointPalette[(index - 1) % waypointPalette.length];
    }
    function assetIdentity(asset) {
      if (asset.domain === 'air') return { color: '#ffcd6e', label: 'A', shape: 'air', path: 'M 0 -12 L 10 10 L 0 5 L -10 10 Z' };
      if (asset.domain === 'ground') return { color: '#9ce37d', label: 'G', shape: 'ground', path: 'M -9 -9 L 9 -9 L 9 9 L -9 9 Z' };
      return { color: '#9bd4ff', label: 'X', shape: 'ground', path: 'M -9 -9 L 9 -9 L 9 9 L -9 9 Z' };
    }
    function normalizeRoute(route) { return (route || []).map((p, i) => ({ label: p.label || (i === 0 ? 'START' : 'WP' + i), lat: Number(p.lat), lon: Number(p.lon), alt: Number(p.alt || 80) })); }
    function setRoute(route) { state.route = normalizeRoute(route); renderWaypointEditor(); drawRoute(); drawFallback(Object.values(state.latestDrones)); updateActionStates(); }
    function addWaypoint(point) { state.route.push({ label: 'WP' + state.route.length, lat: Number(point.lat), lon: Number(point.lon), alt: Number(point.alt || 80) }); setRoute(state.route); }
    function updateWaypoint(index, key, value) { state.route[index][key] = key === 'label' ? value : Number(value); setRoute(state.route); }
    function removeWaypoint(index) { state.route.splice(index, 1); setRoute(state.route); }
    function renderFleetRoster() {
      const roster = $('fleetRoster'); roster.innerHTML = '';
      for (const nodeId of fleetIds()) {
        const latest = state.latestDrones[nodeId];
        const info = fleetInfo(nodeId);
        const card = document.createElement('label');
        const identity = droneIdentity(nodeId);
        card.className = 'droneCard' + (state.selectedNodeIds.has(nodeId) ? ' selected' : '');
        card.style.setProperty('--drone-color', identity.color);
        const stateText = latest ? latest.state : (info.state || 'available');
        const sourceText = latest ? latest.source : (info.source || info.role || 'local-sim');
        const battery = latest ? Number(latest.batteryPercent).toFixed(0) + '%' : (info.batteryPercent != null ? Number(info.batteryPercent).toFixed(0) + '%' : 'ready');
        const callsign = info.callsign && info.callsign !== nodeId ? `${escapeHtml(info.callsign)}<br>` : '';
        card.innerHTML = `<input type="checkbox" ${state.selectedNodeIds.has(nodeId) ? 'checked' : ''}><span class="droneGlyph shape-${identity.shape}">${droneBadge(nodeId)}</span><span>${callsign}${escapeHtml(nodeId)}<br><span class="micro">${escapeHtml(stateText)} · ${escapeHtml(sourceText)}</span></span><span>${battery}</span>`;
        const box = card.querySelector('input');
        box.addEventListener('change', () => { box.checked ? state.selectedNodeIds.add(nodeId) : state.selectedNodeIds.delete(nodeId); renderFleetRoster(); updateActionStates(); });
        roster.appendChild(card);
      }
      updateActionStates();
    }
    function renderWaypointEditor() {
      const el = $('waypoints'); el.innerHTML = '';
      state.route.forEach((point, index) => {
        const row = document.createElement('div'); row.className = 'waypointRow';
        row.style.setProperty('--waypoint-color', waypointColor(index, state.route.length));
        const label = index === 0 ? 'Start' : (index === state.route.length - 1 ? 'End' : `WP${index}`);
        row.innerHTML = `<span class="waypointSwatch"></span><span class="waypointLabel">${label}</span><input type="number" step="0.000001" value="${Number(point.lat).toFixed(6)}"><input type="number" step="0.000001" value="${Number(point.lon).toFixed(6)}"><input type="number" min="0" max="120" value="${Number(point.alt || 80).toFixed(0)}"><button class="danger small">x</button>`;
        const inputs = row.querySelectorAll('input');
        inputs[0].addEventListener('change', e => updateWaypoint(index, 'lat', e.target.value));
        inputs[1].addEventListener('change', e => updateWaypoint(index, 'lon', e.target.value));
        inputs[2].addEventListener('change', e => updateWaypoint(index, 'alt', e.target.value));
        row.querySelector('button').addEventListener('click', () => removeWaypoint(index));
        el.appendChild(row);
      });
    }
    function loadMap() {
      if (!window.DRONEOPS_CONFIG.googleMapsApiKey) { $('fallbackMap').style.display = 'block'; $('map').style.display = 'none'; setRoute(state.route); poll(); return; }
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${window.DRONEOPS_CONFIG.googleMapsApiKey}&callback=initMap`;
      script.async = true; script.onerror = () => { $('fallbackMap').style.display = 'block'; $('map').style.display = 'none'; poll(); };
      document.head.appendChild(script);
    }
    window.initMap = function() {
      state.googleReady = true;
      state.map = new google.maps.Map($('map'), { center: { lat: state.route[0].lat, lng: state.route[0].lon }, zoom: 15, mapTypeId: 'satellite' });
      state.streetService = new google.maps.StreetViewService();
      state.streetPanorama = new google.maps.StreetViewPanorama($('streetView'), { visible: false });
      state.map.addListener('click', event => { if (state.drawMode) addWaypoint({ lat: event.latLng.lat(), lon: event.latLng.lng(), alt: 80 }); });
      setRoute(state.route); poll();
    };
    function drawRoute() {
      if (!state.googleReady || !state.map) return;
      state.routeMarkers.forEach(marker => marker.setMap(null)); state.routeMarkers = [];
      state.routeLines.forEach(line => line.setMap(null)); state.routeLines = [];
      const path = state.route.map(p => ({ lat: p.lat, lng: p.lon }));
      for (let i = 0; i < path.length - 1; i++) {
        state.routeLines.push(new google.maps.Polyline({ path: [path[i], path[i + 1]], map: state.map, strokeColor: waypointColor(i + 1, state.route.length), strokeWeight: 5, strokeOpacity: .92 }));
      }
      path.forEach((position, index) => {
        const marker = new google.maps.Marker({
          position,
          map: state.map,
          draggable: true,
          label: { text: String(index + 1), color: '#071015', fontWeight: '800' },
          icon: {
            path: 'M 0 -12 L 8 -8 L 12 0 L 8 8 L 0 12 L -8 8 L -12 0 L -8 -8 Z',
            scale: 1,
            fillColor: waypointColor(index, state.route.length),
            fillOpacity: 1,
            strokeColor: '#eef4f8',
            strokeWeight: 2
          }
        });
        marker.addListener('dragend', e => updateWaypoint(index, 'lat', e.latLng.lat()));
        marker.addListener('dragend', e => updateWaypoint(index, 'lon', e.latLng.lng()));
        state.routeMarkers.push(marker);
      });
    }
    async function startMission() {
      if (state.route.length < 2 || state.selectedNodeIds.size < 1) { setStatus('Select drones and at least two waypoints.'); return; }
      state.requestBusy = true; updateActionStates(); state.knownExecuting.clear(); closeDroneModal(); closeObservationTooltip();
      try {
        const body = { order: $('order').value, nodeCount: Number($('nodes').value || 4), ticks: Number($('ticks').value || 36), tickSeconds: 0.6, routeWaypoints: state.route, selectedNodeIds: Array.from(state.selectedNodeIds) };
        const response = await fetch('/api/mission/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
        const payload = await response.json(); if (!response.ok) { setStatus('Error: ' + (payload.error || 'start failed')); return; }
        if (payload.mission) setRoute(payload.mission.routeWaypoints || state.route); render(payload);
      } catch (error) {
        setStatus('Start failed: ' + error.message);
      } finally {
        state.requestBusy = false; updateActionStates();
      }
    }
    async function issueLiveOrder(command) {
      state.requestBusy = true; updateActionStates();
      try {
        const response = await fetch('/api/orders/live', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command, targets: Array.from(state.selectedNodeIds) }) });
        const payload = await response.json(); if (!response.ok) { setStatus('Order rejected: ' + (payload.error || 'unknown error')); return; }
        render(payload); setStatus(`Simulated ${command} order issued.`);
      } catch (error) {
        setStatus('Order failed: ' + error.message);
      } finally {
        state.requestBusy = false; updateActionStates();
      }
    }
    async function poll() { try { const response = await fetch('/api/mission'); render(await response.json()); } catch (error) { setStatus('Polling failed: ' + error.message); } setTimeout(poll, 700); }
    function render(payload) {
      state.missionStatus = payload.status || 'idle';
      state.availableDrones = payload.availableDrones || state.availableDrones || [];
      const validIds = new Set(fleetIds());
      state.selectedNodeIds = new Set([...state.selectedNodeIds].filter(id => validIds.has(id)));
      if (!state.selectedNodeIds.size && state.missionStatus === 'idle') state.selectedNodeIds = new Set(generatedFleetIds().filter(id => validIds.has(id)));
      renderPhase(payload);
      setStatus(`Mission: ${state.missionStatus} | tick ${payload.currentTick || 0}/${Math.max(0, (payload.totalTicks || 1) - 1)} | liveExecution=${payload.liveExecution}`);
      $('topics').textContent = (payload.networkTopics || []).join(', ') || 'none';
      renderDrones(payload.atakDrones || []); renderExternalAssets(payload.externalAssets || []); renderObservationReports(payload.observationReports || []); renderFleetRoster(); refreshOpenModal(); drawFallback(payload.atakDrones || []); updateActionStates();
    }
    function renderPhase(payload) {
      const status = payload.status || 'idle';
      const current = Number(payload.currentTick || 0);
      const missionTicks = Number(payload.missionTicks || payload.totalTicks || 1);
      const returnTicks = Number(payload.returnHomeTicks || 0);
      const total = Math.max(1, Number(payload.totalTicks || missionTicks + returnTicks || 1));
      const steps = [
        ['phaseIdle', status !== 'idle'],
        ['phaseRoute', current >= 0 && status !== 'idle'],
        ['phaseReturn', current >= missionTicks],
        ['phaseComplete', status === 'complete']
      ];
      for (const [id, done] of steps) $(id).className = 'phaseStep' + (done ? ' done' : '');
      if (status === 'idle') $('phaseIdle').className = 'phaseStep active';
      else if (status === 'returning_home') $('phaseReturn').className = 'phaseStep active';
      else if (status === 'complete') $('phaseComplete').className = 'phaseStep active';
      else $('phaseRoute').className = 'phaseStep active';
      $('phaseProgress').style.width = `${Math.min(100, Math.max(0, (current / Math.max(1, total - 1)) * 100))}%`;
      if (status === 'returning_home') $('phaseText').textContent = `Returning home ${Math.min(returnTicks, Math.max(0, current - missionTicks + 1))}/${returnTicks}`;
      else if (status === 'complete') $('phaseText').textContent = 'Mission complete. Drones are back at the start point.';
      else if (status === 'running') $('phaseText').textContent = `Route ${Math.min(missionTicks, current + 1)}/${missionTicks}. Automatic RTH follows.`;
      else $('phaseText').textContent = 'Plan a route and start the simulation.';
    }
    function renderDrones(drones) {
      const el = $('drones'); el.innerHTML = ''; const seen = new Set();
      for (const drone of drones) {
        seen.add(drone.nodeId); state.latestDrones[drone.nodeId] = drone;
        const row = document.createElement('div'); row.className = 'row';
        const identity = droneIdentity(drone.nodeId);
        row.style.borderColor = identity.color;
        row.innerHTML = `<span><span class="droneGlyph shape-${identity.shape}" style="--drone-color:${identity.color}; display:inline-grid; margin-right:8px; vertical-align:middle;">D${droneNumber(drone.nodeId)}</span>${drone.nodeId}<br><span class="micro">${drone.state}</span></span><span>${Number(drone.lat).toFixed(5)}, ${Number(drone.lon).toFixed(5)}<br>${Number(drone.batteryPercent).toFixed(0)}%</span>`;
        el.appendChild(row);
        if (state.googleReady && state.map) {
          const pos = { lat: Number(drone.lat), lng: Number(drone.lon) };
          const markerIcon = { path: identity.path, scale: 1.15, fillColor: identity.color, fillOpacity: .96, strokeColor: '#071015', strokeWeight: 2 };
          if (!state.droneMarkers[drone.nodeId]) {
            state.droneMarkers[drone.nodeId] = new google.maps.Marker({ position: pos, map: state.map, label: { text: String(droneNumber(drone.nodeId)), color: '#071015', fontWeight: '800' }, icon: markerIcon, title: drone.nodeId });
            state.droneMarkers[drone.nodeId].addListener('click', () => openDroneModal(state.latestDrones[drone.nodeId] || drone, 'click'));
            state.droneMarkers[drone.nodeId].addListener('mouseover', () => openDroneModal(state.latestDrones[drone.nodeId] || drone, 'hover'));
            state.droneMarkers[drone.nodeId].addListener('mouseout', () => closeHoverDroneModal(drone.nodeId));
          }
          state.droneMarkers[drone.nodeId].setPosition(pos);
          state.droneMarkers[drone.nodeId].setIcon(markerIcon);
        }
      }
      if (state.googleReady && state.map) for (const [id, marker] of Object.entries(state.droneMarkers)) if (!seen.has(id)) { marker.setMap(null); delete state.droneMarkers[id]; }
    }
    function renderExternalAssets(assets) {
      const el = $('assets'); el.innerHTML = ''; const seen = new Set();
      for (const asset of assets) {
        seen.add(asset.uid); state.latestAssets[asset.uid] = asset;
        const identity = assetIdentity(asset);
        const row = document.createElement('div'); row.className = 'row';
        row.style.borderColor = identity.color;
        row.innerHTML = `<span><span class="assetGlyph asset-${identity.shape}" style="--asset-color:${identity.color};">${identity.label}</span>${asset.callsign}<br><span class="micro">${asset.domain} ${asset.kind} - read-only</span></span><span>${Number(asset.position.lat).toFixed(5)}, ${Number(asset.position.lon).toFixed(5)}<br>${asset.status}</span>`;
        el.appendChild(row);
        if (state.googleReady && state.map) {
          const pos = { lat: Number(asset.position.lat), lng: Number(asset.position.lon) };
          const markerIcon = { path: identity.path, scale: 1.05, fillColor: identity.color, fillOpacity: asset.domain === 'air' ? .96 : .18, strokeColor: identity.color, strokeWeight: 2 };
          if (!state.assetMarkers[asset.uid]) {
            state.assetMarkers[asset.uid] = new google.maps.Marker({ position: pos, map: state.map, label: { text: identity.label, color: asset.domain === 'air' ? '#071015' : identity.color, fontWeight: '800' }, icon: markerIcon, title: `${asset.callsign} (read-only)` });
          }
          state.assetMarkers[asset.uid].setPosition(pos);
          state.assetMarkers[asset.uid].setIcon(markerIcon);
        }
      }
      if (state.googleReady && state.map) for (const [id, marker] of Object.entries(state.assetMarkers)) if (!seen.has(id)) { marker.setMap(null); delete state.assetMarkers[id]; }
    }
    function renderObservationReports(reports) {
      const el = $('observations'); el.innerHTML = ''; const seen = new Set();
      for (const report of reports) {
        seen.add(report.reportId); state.latestObservations[report.reportId] = report;
        const position = report.position || {};
        const row = document.createElement('div'); row.className = 'row observationRow';
        row.innerHTML = `<img class="observationThumb" alt="Observation thumbnail" src="${report.imageDataUri || ''}"><span><span class="observationPin"><span>!</span></span>${escapeHtml(report.label)}<br><span class="micro">${escapeHtml(report.reportingNodeId)} - ${Number(report.confidence || 0).toFixed(2)} confidence</span><br><span class="micro">${Number(position.lat).toFixed(5)}, ${Number(position.lon).toFixed(5)}</span></span>`;
        row.addEventListener('click', () => openObservationTooltip(report));
        el.appendChild(row);
        if (state.googleReady && state.map) {
          const pos = { lat: Number(position.lat), lng: Number(position.lon) };
          const markerIcon = { path: 'M 0 -16 C 9 -16 16 -9 16 0 C 16 10 0 20 0 20 C 0 20 -16 10 -16 0 C -16 -9 -9 -16 0 -16 Z', scale: .9, fillColor: '#ff7a68', fillOpacity: .96, strokeColor: '#071015', strokeWeight: 2 };
          if (!state.observationMarkers[report.reportId]) {
            state.observationMarkers[report.reportId] = new google.maps.Marker({ position: pos, map: state.map, label: { text: '!', color: '#071015', fontWeight: '900' }, icon: markerIcon, title: `${report.label} from ${report.reportingNodeId}` });
            state.observationMarkers[report.reportId].addListener('click', () => openObservationTooltip(state.latestObservations[report.reportId] || report));
          }
          state.observationMarkers[report.reportId].setPosition(pos);
          state.observationMarkers[report.reportId].setIcon(markerIcon);
        }
      }
      if (!reports.length) el.innerHTML = '<div class="micro">No reports yet. Start a simulation and sightings will appear here.</div>';
      for (const id of Object.keys(state.latestObservations)) if (!seen.has(id)) delete state.latestObservations[id];
      if (state.googleReady && state.map) for (const [id, marker] of Object.entries(state.observationMarkers)) if (!seen.has(id)) { marker.setMap(null); delete state.observationMarkers[id]; }
    }
    function openDroneModal(drone, trigger) {
      if (trigger === 'hover' && state.followDroneId && state.followDroneId !== drone.nodeId) return;
      state.selectedDroneId = drone.nodeId;
      if (trigger === 'click') state.followDroneId = drone.nodeId;
      $('droneModal').classList.add('open');
      $('droneModal').setAttribute('aria-hidden', 'false');
      renderDroneModal(drone);
      updateTooltipView(drone);
    }
    function closeDroneModal() { $('droneModal').classList.remove('open'); $('droneModal').setAttribute('aria-hidden', 'true'); state.selectedDroneId = null; state.followDroneId = null; state.tooltipAnchor = null; if (state.streetPanorama) state.streetPanorama.setVisible(false); }
    function closeHoverDroneModal(nodeId) { if (!state.followDroneId && state.selectedDroneId === nodeId) closeDroneModal(); }
    function unfollowDrone() { state.followDroneId = null; if (state.selectedDroneId && state.latestDrones[state.selectedDroneId]) renderDroneModal(state.latestDrones[state.selectedDroneId]); }
    function openObservationTooltip(report) {
      const position = report.position || {};
      state.selectedObservationId = report.reportId;
      $('observationTitle').textContent = report.label || 'Observation';
      $('observationImage').src = report.imageDataUri || '';
      $('observationDetails').innerHTML = [
        ['Reporting drone', escapeHtml(report.reportingNodeId)],
        ['Coordinates', `${Number(position.lat).toFixed(7)}, ${Number(position.lon).toFixed(7)}`],
        ['Altitude', `${Number(position.alt || 0).toFixed(1)} m`],
        ['Confidence', Number(report.confidence || 0).toFixed(2)],
        ['Category', escapeHtml(report.category || 'unknown')],
        ['Received', escapeHtml(report.timestamp || 'n/a')]
      ].map(([k, v]) => `<div class="param"><span>${k}</span><span>${v}</span></div>`).join('');
      $('observationTooltip').classList.add('open');
      $('observationTooltip').setAttribute('aria-hidden', 'false');
      positionObservationTooltip(report);
    }
    function closeObservationTooltip() { $('observationTooltip').classList.remove('open'); $('observationTooltip').setAttribute('aria-hidden', 'true'); state.observationAnchor = null; state.selectedObservationId = null; }
    function positionObservationTooltip(report) {
      let point = null;
      if (state.googleReady && state.map && state.observationMarkers[report.reportId]) point = googleMarkerScreenPoint(state.observationMarkers[report.reportId]);
      else {
        const hit = state.fallbackObservationHits.find(item => item.reportId === report.reportId);
        if (hit) point = fallbackScreenPoint(hit.x, hit.y);
      }
      if (!point) return;
      state.observationAnchor = point;
      const tooltip = $('observationTooltip');
      const panel = tooltip.querySelector('.modalPanel');
      const panelWidth = panel ? panel.offsetWidth || 300 : 300;
      const panelHeight = panel ? panel.offsetHeight || 250 : 250;
      let left = point.x + 16;
      let top = point.y;
      if (left + panelWidth > window.innerWidth - 8) left = point.x - panelWidth - 16;
      top = Math.max(8 + panelHeight / 2, Math.min(window.innerHeight - 8 - panelHeight / 2, top));
      tooltip.style.left = `${Math.max(8, left)}px`;
      tooltip.style.top = `${top}px`;
      tooltip.style.transform = 'translate(0, -50%)';
    }
    function refreshOpenModal() {
      const activeId = state.followDroneId || state.selectedDroneId;
      if (activeId && state.latestDrones[activeId]) {
        state.selectedDroneId = activeId;
        renderDroneModal(state.latestDrones[activeId]);
        updateTooltipView(state.latestDrones[activeId]);
      }
      if (state.selectedObservationId && state.latestObservations[state.selectedObservationId]) positionObservationTooltip(state.latestObservations[state.selectedObservationId]);
    }
    function renderDroneModal(drone) {
      $('modalTitle').textContent = `${drone.nodeId} live view`;
      $('modalStatus').textContent = state.followDroneId === drone.nodeId ? 'Pinned simulated local view.' : 'Simulated local view.';
      $('unfollowBtn').style.display = state.followDroneId === drone.nodeId ? 'inline-block' : 'none';
      const values = [['State', drone.state], ['Mission', drone.missionId || 'none'], ['Latitude', Number(drone.lat).toFixed(7)], ['Longitude', Number(drone.lon).toFixed(7)], ['Altitude', `${Number(drone.alt).toFixed(1)} m`], ['Battery', `${Number(drone.batteryPercent).toFixed(1)}%`], ['Source', drone.source], ['UID', drone.uid], ['Live exec', String(drone.liveExecution)], ['Last seen', drone.lastSeenIso || 'n/a']];
      $('paramGrid').innerHTML = values.map(([k, v]) => `<div class="param"><span>${k}</span><span>${v}</span></div>`).join('');
    }
    function updateTooltipView(drone) {
      positionDroneTooltip(drone);
      updateStreetView(drone);
    }
    function positionDroneTooltip(drone) {
      let point = null;
      if (state.googleReady && state.map && state.droneMarkers[drone.nodeId]) {
        point = googleMarkerScreenPoint(state.droneMarkers[drone.nodeId]);
      } else {
        const hit = state.fallbackDroneHits.find(item => item.nodeId === drone.nodeId);
        if (hit) point = fallbackScreenPoint(hit.x, hit.y);
      }
      if (!point) return;
      state.tooltipAnchor = point;
      const tooltip = $('droneModal');
      const panel = tooltip.querySelector('.modalPanel');
      const panelWidth = panel ? panel.offsetWidth || 310 : 310;
      const panelHeight = panel ? panel.offsetHeight || 300 : 300;
      let left = point.x + 16;
      let top = point.y;
      if (left + panelWidth > window.innerWidth - 8) left = point.x - panelWidth - 16;
      top = Math.max(8 + panelHeight / 2, Math.min(window.innerHeight - 8 - panelHeight / 2, top));
      tooltip.style.left = `${Math.max(8, left)}px`;
      tooltip.style.top = `${top}px`;
      tooltip.style.transform = left < point.x ? 'translate(0, -50%)' : 'translate(0, -50%)';
    }
    function googleMarkerScreenPoint(marker) {
      if (!state.googleReady || !state.map || !marker.getPosition) return null;
      if (!state.tooltipProjection) {
        state.tooltipProjection = new google.maps.OverlayView();
        state.tooltipProjection.onAdd = function() {};
        state.tooltipProjection.draw = function() {};
        state.tooltipProjection.onRemove = function() {};
        state.tooltipProjection.setMap(state.map);
      }
      const projection = state.tooltipProjection.getProjection && state.tooltipProjection.getProjection();
      if (!projection) return null;
      const pixel = projection.fromLatLngToContainerPixel(marker.getPosition());
      const rect = state.map.getDiv().getBoundingClientRect();
      return { x: rect.left + pixel.x, y: rect.top + pixel.y };
    }
    function fallbackScreenPoint(x, y) {
      const canvas = $('fallbackMap');
      const rect = canvas.getBoundingClientRect();
      return { x: rect.left + (x / Math.max(1, canvas.width)) * rect.width, y: rect.top + (y / Math.max(1, canvas.height)) * rect.height };
    }
    function updateStreetView(drone) {
      if (!(state.googleReady && state.streetService && state.streetPanorama)) { $('streetView').style.display = 'none'; $('streetFallback').style.display = 'flex'; return; }
      const pos = { lat: Number(drone.lat), lng: Number(drone.lon) };
      const now = Date.now(); const last = state.streetLast;
      if (last.nodeId === drone.nodeId && Math.abs(Number(last.lat || 0) - pos.lat) < 0.00025 && Math.abs(Number(last.lon || 0) - pos.lng) < 0.00025 && now - last.at < 3500) return;
      state.streetLast = { nodeId: drone.nodeId, lat: pos.lat, lon: pos.lng, at: now };
      state.streetService.getPanorama({ location: pos, radius: 100 }).then(({ data }) => { state.streetPanorama.setPano(data.location.pano); state.streetPanorama.setPov({ heading: 270, pitch: 0 }); state.streetPanorama.setVisible(true); $('streetFallback').style.display = 'none'; }).catch(() => { state.streetPanorama.setVisible(false); $('streetFallback').style.display = 'flex'; $('streetFallback').textContent = `No Street View imagery near ${Number(drone.lat).toFixed(5)}, ${Number(drone.lon).toFixed(5)}.`; });
    }
    function drawFallback(drones) {
      if (state.googleReady) return;
      const canvas = $('fallbackMap'); canvas.style.display = 'block'; const shell = $('mapShell'); canvas.width = shell.clientWidth || 900; canvas.height = shell.clientHeight || 600;
      const ctx = canvas.getContext('2d'); ctx.fillStyle = '#090d10'; ctx.fillRect(0, 0, canvas.width, canvas.height);
      const assets = Object.values(state.latestAssets);
      const observations = Object.values(state.latestObservations);
      const route = state.route.length ? state.route : window.DRONEOPS_CONFIG.defaultRoute; const all = [...route, ...drones.map(d => ({ lat: d.lat, lon: d.lon })), ...assets.map(a => ({ lat: a.position.lat, lon: a.position.lon })), ...observations.map(r => ({ lat: r.position.lat, lon: r.position.lon }))];
      const lats = all.map(p => Number(p.lat)); const lons = all.map(p => Number(p.lon)); const bounds = { minLat: Math.min(...lats) - .001, maxLat: Math.max(...lats) + .001, minLon: Math.min(...lons) - .001, maxLon: Math.max(...lons) + .001 };
      const rect = { x: 50, y: 50, width: canvas.width - 100, height: canvas.height - 100 }; const project = p => ({ x: rect.x + ((Number(p.lon) - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * rect.width, y: rect.y + rect.height - ((Number(p.lat) - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * rect.height });
      state.fallbackProjection = { bounds, rect };
      ctx.lineWidth = 5;
      for (let i = 0; i < route.length - 1; i++) { const a = project(route[i]); const b = project(route[i + 1]); ctx.strokeStyle = waypointColor(i + 1, route.length); ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
      route.forEach((point, i) => { const p = project(point); ctx.fillStyle = waypointColor(i, route.length); ctx.strokeStyle = '#eef4f8'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(p.x, p.y, 8, 0, Math.PI * 2); ctx.fill(); ctx.stroke(); ctx.fillStyle = '#071015'; ctx.font = '700 10px Arial'; ctx.textAlign = 'center'; ctx.fillText(String(i + 1), p.x, p.y + 3); });
      state.fallbackDroneHits = [];
      drones.forEach(drone => {
        const p = project({ lat: drone.lat, lon: drone.lon });
        const identity = droneIdentity(drone.nodeId);
        drawCanvasDrone(ctx, p.x, p.y, identity, droneNumber(drone.nodeId));
        state.fallbackDroneHits.push({ nodeId: drone.nodeId, x: p.x, y: p.y, radius: 16 });
        ctx.fillStyle = '#eef4f8'; ctx.font = '12px Arial'; ctx.textAlign = 'left'; ctx.fillText(drone.nodeId, p.x + 14, p.y + 4);
      });
      assets.forEach(asset => {
        const p = project({ lat: asset.position.lat, lon: asset.position.lon });
        const identity = assetIdentity(asset);
        drawCanvasAsset(ctx, p.x, p.y, identity);
        ctx.fillStyle = '#dfe9ef'; ctx.font = '12px Arial'; ctx.textAlign = 'left'; ctx.fillText(asset.callsign, p.x + 14, p.y + 4);
      });
      state.fallbackObservationHits = [];
      observations.forEach(report => {
        const p = project({ lat: report.position.lat, lon: report.position.lon });
        drawCanvasObservation(ctx, p.x, p.y);
        state.fallbackObservationHits.push({ reportId: report.reportId, x: p.x, y: p.y, radius: 18 });
        ctx.fillStyle = '#fff4ed'; ctx.font = '12px Arial'; ctx.textAlign = 'left'; ctx.fillText(report.label, p.x + 14, p.y + 4);
      });
    }
    function drawCanvasDrone(ctx, x, y, identity, number) {
      ctx.save(); ctx.translate(x, y); ctx.fillStyle = identity.color; ctx.strokeStyle = '#071015'; ctx.lineWidth = 2; ctx.beginPath();
      if (identity.shape === 'triangle') { ctx.moveTo(0, -12); ctx.lineTo(11, 11); ctx.lineTo(0, 6); ctx.lineTo(-11, 11); }
      else if (identity.shape === 'diamond') { ctx.moveTo(0, -12); ctx.lineTo(12, 0); ctx.lineTo(0, 12); ctx.lineTo(-12, 0); }
      else if (identity.shape === 'square') { ctx.rect(-10, -10, 20, 20); }
      else if (identity.shape === 'hex') { ctx.moveTo(0, -12); ctx.lineTo(10, -6); ctx.lineTo(10, 6); ctx.lineTo(0, 12); ctx.lineTo(-10, 6); ctx.lineTo(-10, -6); }
      else if (identity.shape === 'kite') { ctx.moveTo(0, -13); ctx.lineTo(10, -2); ctx.lineTo(4, 12); ctx.lineTo(-4, 12); ctx.lineTo(-10, -2); }
      else { ctx.arc(0, 0, 11, 0, Math.PI * 2); }
      ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.fillStyle = '#071015'; ctx.font = '800 10px Arial'; ctx.textAlign = 'center'; ctx.fillText(String(number), 0, 4); ctx.restore();
    }
    function drawCanvasAsset(ctx, x, y, identity) {
      ctx.save(); ctx.translate(x, y); ctx.strokeStyle = identity.color; ctx.fillStyle = identity.shape === 'air' ? identity.color : 'rgba(16,21,26,.92)'; ctx.lineWidth = 2; ctx.beginPath();
      if (identity.shape === 'air') { ctx.moveTo(0, -12); ctx.lineTo(10, 10); ctx.lineTo(0, 5); ctx.lineTo(-10, 10); }
      else { ctx.rect(-9, -9, 18, 18); }
      ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.fillStyle = identity.shape === 'air' ? '#071015' : identity.color; ctx.font = '800 10px Arial'; ctx.textAlign = 'center'; ctx.fillText(identity.label, 0, 4); ctx.restore();
    }
    function drawCanvasObservation(ctx, x, y) {
      ctx.save(); ctx.translate(x, y); ctx.fillStyle = '#ff7a68'; ctx.strokeStyle = '#071015'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(0, -4, 11, 0, Math.PI * 2); ctx.moveTo(-5, 6); ctx.lineTo(0, 16); ctx.lineTo(5, 6); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.fillStyle = '#071015'; ctx.font = '900 12px Arial'; ctx.textAlign = 'center'; ctx.fillText('!', 0, 0); ctx.restore();
    }
    function fallbackHit(event) {
      const rect = $('fallbackMap').getBoundingClientRect();
      const scaleX = $('fallbackMap').width / Math.max(1, rect.width);
      const scaleY = $('fallbackMap').height / Math.max(1, rect.height);
      const x = (event.clientX - rect.left) * scaleX;
      const y = (event.clientY - rect.top) * scaleY;
      return state.fallbackDroneHits.find(hit => Math.hypot(hit.x - x, hit.y - y) <= hit.radius);
    }
    function fallbackObservationHit(event) {
      const rect = $('fallbackMap').getBoundingClientRect();
      const scaleX = $('fallbackMap').width / Math.max(1, rect.width);
      const scaleY = $('fallbackMap').height / Math.max(1, rect.height);
      const x = (event.clientX - rect.left) * scaleX;
      const y = (event.clientY - rect.top) * scaleY;
      return state.fallbackObservationHits.find(hit => Math.hypot(hit.x - x, hit.y - y) <= hit.radius);
    }
    function fallbackRoutePoint(event) {
      if (!state.fallbackProjection) return null;
      const canvas = $('fallbackMap');
      const box = canvas.getBoundingClientRect();
      const x = (event.clientX - box.left) * (canvas.width / Math.max(1, box.width));
      const y = (event.clientY - box.top) * (canvas.height / Math.max(1, box.height));
      const { bounds, rect } = state.fallbackProjection;
      const fractionX = Math.min(1, Math.max(0, (x - rect.x) / rect.width));
      const fractionY = Math.min(1, Math.max(0, (y - rect.y) / rect.height));
      return {
        lat: bounds.maxLat - fractionY * (bounds.maxLat - bounds.minLat),
        lon: bounds.minLon + fractionX * (bounds.maxLon - bounds.minLon),
        alt: state.route.length ? state.route[state.route.length - 1].alt : 80
      };
    }
    function openFallbackDrone(event) {
      const hit = fallbackHit(event);
      if (hit && state.latestDrones[hit.nodeId]) openDroneModal(state.latestDrones[hit.nodeId], event.type === 'click' ? 'click' : 'hover');
    }
    function openFallbackObservation(event) {
      const hit = fallbackObservationHit(event);
      if (hit && state.latestObservations[hit.reportId]) openObservationTooltip(state.latestObservations[hit.reportId]);
    }
    $('startBtn').addEventListener('click', startMission);
    $('selectAllBtn').addEventListener('click', () => { state.selectedNodeIds = new Set(fleetIds()); renderFleetRoster(); });
    $('selectNoneBtn').addEventListener('click', () => { state.selectedNodeIds = new Set(); renderFleetRoster(); });
    $('nodes').addEventListener('change', () => { const ids = new Set(fleetIds()); state.selectedNodeIds = new Set([...state.selectedNodeIds].filter(id => ids.has(id))); renderFleetRoster(); });
    $('addWaypointBtn').addEventListener('click', () => { const last = state.route[state.route.length - 1] || window.DRONEOPS_CONFIG.defaultRoute[0]; addWaypoint({ lat: Number(last.lat) + 0.001, lon: Number(last.lon) + 0.001, alt: Number(last.alt || 80) }); });
    $('resetRouteBtn').addEventListener('click', () => setRoute(window.DRONEOPS_CONFIG.defaultRoute));
    $('clearRouteBtn').addEventListener('click', () => { if (!state.route.length) return; if (!confirm('Clear all waypoints?')) return; state.lastRouteBeforeClear = state.route.map(point => ({ ...point })); $('undoClearBtn').style.display = 'inline-block'; setRoute([]); });
    $('undoClearBtn').addEventListener('click', () => { if (!state.lastRouteBeforeClear) return; setRoute(state.lastRouteBeforeClear); state.lastRouteBeforeClear = null; $('undoClearBtn').style.display = 'none'; });
    $('drawModeBtn').addEventListener('click', () => { state.drawMode = !state.drawMode; $('drawModeBtn').textContent = state.drawMode ? 'Drawing On' : 'Drawing Off'; $('drawModeBtn').className = state.drawMode ? 'small' : 'secondary small'; });
    $('holdBtn').addEventListener('click', () => issueLiveOrder('hold')); $('resumeBtn').addEventListener('click', () => issueLiveOrder('resume')); $('returnBtn').addEventListener('click', () => issueLiveOrder('return_to_start'));
    $('fallbackMap').addEventListener('click', event => {
      const observationHit = fallbackObservationHit(event);
      if (observationHit) { openFallbackObservation(event); return; }
      const hit = fallbackHit(event);
      if (hit) { openFallbackDrone(event); return; }
      if (state.drawMode) {
        const point = fallbackRoutePoint(event);
        if (point) addWaypoint(point);
      }
    });
    $('fallbackMap').addEventListener('mousemove', event => { const observationHit = fallbackObservationHit(event); const hit = fallbackHit(event); $('fallbackMap').style.cursor = (hit || observationHit) ? 'pointer' : (state.drawMode ? 'crosshair' : 'default'); if (hit) openFallbackDrone(event); else if (!state.followDroneId && state.selectedDroneId) closeDroneModal(); });
    $('unfollowBtn').addEventListener('click', unfollowDrone); $('closeModalBtn').addEventListener('click', closeDroneModal); $('closeObservationBtn').addEventListener('click', closeObservationTooltip); window.addEventListener('resize', () => drawFallback(Object.values(state.latestDrones)));
    renderFleetRoster(); renderWaypointEditor(); updateActionStates(); loadMap();
  </script>
</body>
</html>
"""


def render_index_html(google_maps_api_key, default_route):
    config = {
        "googleMapsApiKey": google_maps_api_key,
        "defaultRoute": default_route,
    }
    return HTML.replace("__CONFIG__", json.dumps(config))
