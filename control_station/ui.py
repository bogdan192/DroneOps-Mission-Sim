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
    .rows { display: grid; gap: 8px; margin-top: 10px; }
    .row, .droneCard { display: grid; grid-template-columns: 1fr auto; gap: 8px; padding: 8px; border: 1px solid #303943; border-radius: 6px; background: #151b20; font-size: 13px; cursor: pointer; transition: border-color .15s ease, background .15s ease, transform .15s ease; }
    .row:hover, .droneCard:hover { border-color: #587183; background: #18232a; }
    .droneCard { grid-template-columns: auto auto 1fr auto; align-items: center; }
    .droneCard.selected { border-color: var(--drone-color); background: #17251f; box-shadow: inset 3px 0 0 var(--drone-color); }
    .droneCard input { width: auto; }
    .droneGlyph { width: 24px; height: 24px; display: grid; place-items: center; background: var(--drone-color); color: #071015; font-size: 11px; font-weight: 800; box-shadow: 0 0 0 2px rgba(255,255,255,.08), 0 8px 18px rgba(0,0,0,.28); }
    .shape-triangle { clip-path: polygon(50% 0, 100% 100%, 50% 72%, 0 100%); }
    .shape-diamond { clip-path: polygon(50% 0, 100% 50%, 50% 100%, 0 50%); }
    .shape-square { border-radius: 5px; }
    .shape-hex { clip-path: polygon(25% 4%, 75% 4%, 100% 50%, 75% 96%, 25% 96%, 0 50%); }
    .shape-circle { border-radius: 50%; }
    .shape-kite { clip-path: polygon(50% 0, 90% 42%, 58% 100%, 42% 100%, 10% 42%); }
    .waypointRow { display: grid; grid-template-columns: 18px 1fr 1fr 68px 30px; gap: 6px; align-items: center; margin-top: 6px; }
    .waypointRow input { padding: 7px; font-size: 12px; }
    .waypointSwatch { width: 14px; height: 14px; border-radius: 50%; background: var(--waypoint-color); box-shadow: 0 0 0 2px rgba(255,255,255,.12); }
    #mapShell { position: relative; min-height: 0; background: #090d10; }
    #map { position: absolute; inset: 0; }
    #fallbackMap { position: absolute; inset: 0; width: 100%; height: 100%; display: none; }
    .mapTools { position: absolute; z-index: 5; top: 12px; left: 12px; display: flex; gap: 8px; flex-wrap: wrap; }
    .modal { position: fixed; inset: 0; display: none; align-items: flex-start; justify-content: flex-end; z-index: 20; background: rgba(0,0,0,.28); padding: 16px; pointer-events: none; }
    .modal.open { display: flex; }
    .modalPanel { width: min(430px, 94vw); max-height: min(620px, 92vh); display: grid; grid-template-rows: auto 1fr; border: 1px solid #3a4650; border-radius: 8px; background: #151b20; overflow: hidden; box-shadow: 0 18px 60px rgba(0,0,0,.42); pointer-events: auto; }
    .modalHead { display: flex; justify-content: space-between; align-items: center; padding: 9px 10px; border-bottom: 1px solid #303943; }
    .modalHead h2 { margin: 0; font-size: 15px; }
    .modalHead button { width: auto; margin: 0; }
    .modalBody { display: grid; grid-template-rows: auto 210px; min-height: 0; }
    .paramPanel { padding: 10px; overflow: auto; border-bottom: 1px solid #303943; }
    .param { display: grid; grid-template-columns: 92px 1fr; gap: 7px; padding: 6px 7px; margin-top: 6px; border: 1px solid #303943; border-radius: 6px; background: #10151a; font-size: 12px; }
    .param span:first-child { color: #9eacb7; }
    #streetView, #streetFallback { min-height: 210px; }
    #streetFallback { display: flex; align-items: center; justify-content: center; padding: 18px; color: #cbd5dd; text-align: center; font-size: 12px; }
    @media (max-width: 820px) { main { grid-template-columns: 1fr; grid-template-rows: auto 55vh; } aside { border-right: 0; border-bottom: 1px solid #303943; } .modal { align-items: flex-start; justify-content: center; } }
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
        <div><label for="ticks">Ticks</label><input id="ticks" type="number" min="2" max="300" value="36"></div>
      </div>
      <div class="panel">
        <div class="panelTitle"><span>Fleet Selection</span><button id="selectAllBtn" class="secondary small">All</button></div>
        <div class="micro">Select drones for the next simulated mission or live order.</div>
        <div id="fleetRoster" class="rows"></div>
      </div>
      <div class="panel">
        <div class="panelTitle"><span>Mission Waypoints</span><button id="resetRouteBtn" class="secondary small">Reset</button></div>
        <div class="micro">Click the map while drawing is on, or edit waypoint values directly.</div>
        <div id="waypoints"></div>
        <div class="grid2"><button id="addWaypointBtn" class="secondary">Add Waypoint</button><button id="clearRouteBtn" class="danger">Clear</button></div>
      </div>
      <button id="startBtn">Issue Mission To Selected</button>
      <div class="panel">
        <div class="panelTitle"><span>Simulated Live Orders</span></div>
        <div class="micro">These orders update simulator state only.</div>
        <div class="grid3"><button id="holdBtn" class="warning">Hold</button><button id="resumeBtn" class="secondary">Resume</button><button id="returnBtn" class="danger">RTL</button></div>
      </div>
      <div id="status" class="status">Ready.</div>
      <label>Tracked ATAK Drones</label><div id="drones" class="rows"></div>
      <label>Network Topics</label><div id="topics" class="status">none</div>
    </aside>
    <section id="mapShell">
      <div class="mapTools"><button id="drawModeBtn" class="secondary small">Drawing On</button><button id="sendSelectedBtn" class="small">Send Selected</button></div>
      <div id="map"></div><canvas id="fallbackMap"></canvas>
    </section>
  </main>
  <div id="droneModal" class="modal" aria-hidden="true">
    <div class="modalPanel">
      <div class="modalHead"><h2 id="modalTitle">Drone</h2><button id="closeModalBtn" class="secondary">Close</button></div>
      <div class="modalBody"><section class="paramPanel"><div id="modalStatus" class="status">Simulated onboard parameters</div><div id="paramGrid"></div></section><section><div id="streetView"></div><div id="streetFallback">Street View imagery will appear here when available.</div></section></div>
    </div>
  </div>
  <script>
    window.DRONEOPS_CONFIG = __CONFIG__;
    const state = {
      map: null, googleReady: false, streetService: null, streetPanorama: null,
      route: window.DRONEOPS_CONFIG.defaultRoute.map(p => ({ ...p })),
      selectedNodeIds: new Set(['drone-01', 'drone-02', 'drone-03', 'drone-04']),
      latestDrones: {}, droneMarkers: {}, routeMarkers: [], routeLines: [],
      drawMode: true, selectedDroneId: null, knownExecuting: new Set(),
      streetLast: { nodeId: null, lat: null, lon: null, at: 0 }
    };
    const $ = id => document.getElementById(id);
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
    function droneNumber(nodeId) { return Math.max(1, Number(String(nodeId).split('-')[1] || 1)); }
    function droneIdentity(nodeId) { return dronePalette[(droneNumber(nodeId) - 1) % dronePalette.length]; }
    function waypointColor(index, total) {
      if (index === 0) return '#41d68b';
      if (index === total - 1) return '#ff7a68';
      return waypointPalette[(index - 1) % waypointPalette.length];
    }
    function normalizeRoute(route) { return (route || []).map((p, i) => ({ label: p.label || (i === 0 ? 'START' : 'WP' + i), lat: Number(p.lat), lon: Number(p.lon), alt: Number(p.alt || 80) })); }
    function setRoute(route) { state.route = normalizeRoute(route); renderWaypointEditor(); drawRoute(); drawFallback(Object.values(state.latestDrones)); }
    function addWaypoint(point) { state.route.push({ label: 'WP' + state.route.length, lat: Number(point.lat), lon: Number(point.lon), alt: Number(point.alt || 80) }); setRoute(state.route); }
    function updateWaypoint(index, key, value) { state.route[index][key] = key === 'label' ? value : Number(value); setRoute(state.route); }
    function removeWaypoint(index) { state.route.splice(index, 1); setRoute(state.route); }
    function fleetIds() { const count = Math.max(1, Math.min(12, Number($('nodes').value || 4))); return Array.from({ length: count }, (_, i) => `drone-${String(i + 1).padStart(2, '0')}`); }
    function renderFleetRoster() {
      const roster = $('fleetRoster'); roster.innerHTML = '';
      for (const nodeId of fleetIds()) {
        const latest = state.latestDrones[nodeId];
        const card = document.createElement('label');
        const identity = droneIdentity(nodeId);
        card.className = 'droneCard' + (state.selectedNodeIds.has(nodeId) ? ' selected' : '');
        card.style.setProperty('--drone-color', identity.color);
        card.innerHTML = `<input type="checkbox" ${state.selectedNodeIds.has(nodeId) ? 'checked' : ''}><span class="droneGlyph shape-${identity.shape}">D${droneNumber(nodeId)}</span><span>${nodeId}<br><span class="micro">${latest ? latest.state : 'available'}</span></span><span>${latest ? Number(latest.batteryPercent).toFixed(0) + '%' : 'ready'}</span>`;
        const box = card.querySelector('input');
        box.addEventListener('change', () => { box.checked ? state.selectedNodeIds.add(nodeId) : state.selectedNodeIds.delete(nodeId); renderFleetRoster(); });
        roster.appendChild(card);
      }
    }
    function renderWaypointEditor() {
      const el = $('waypoints'); el.innerHTML = '';
      state.route.forEach((point, index) => {
        const row = document.createElement('div'); row.className = 'waypointRow';
        row.style.setProperty('--waypoint-color', waypointColor(index, state.route.length));
        row.innerHTML = `<span class="waypointSwatch"></span><input type="number" step="0.000001" value="${Number(point.lat).toFixed(6)}"><input type="number" step="0.000001" value="${Number(point.lon).toFixed(6)}"><input type="number" min="0" max="120" value="${Number(point.alt || 80).toFixed(0)}"><button class="danger small">x</button>`;
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
      state.knownExecuting.clear(); closeDroneModal();
      const body = { order: $('order').value, nodeCount: Number($('nodes').value || 4), ticks: Number($('ticks').value || 36), tickSeconds: 0.6, routeWaypoints: state.route, selectedNodeIds: Array.from(state.selectedNodeIds) };
      const response = await fetch('/api/mission/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const payload = await response.json(); if (!response.ok) { setStatus('Error: ' + (payload.error || 'start failed')); return; }
      if (payload.mission) setRoute(payload.mission.routeWaypoints || state.route); render(payload);
    }
    async function issueLiveOrder(command) {
      const response = await fetch('/api/orders/live', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command, targets: Array.from(state.selectedNodeIds) }) });
      const payload = await response.json(); if (!response.ok) { setStatus('Order rejected: ' + (payload.error || 'unknown error')); return; }
      render(payload); setStatus(`Simulated ${command} order issued.`);
    }
    async function poll() { try { const response = await fetch('/api/mission'); render(await response.json()); } catch (error) { setStatus('Polling failed: ' + error.message); } setTimeout(poll, 700); }
    function render(payload) {
      setStatus(`Mission: ${payload.status || 'idle'} | tick ${payload.currentTick || 0}/${Math.max(0, (payload.totalTicks || 1) - 1)} | liveExecution=${payload.liveExecution}`);
      $('topics').textContent = (payload.networkTopics || []).join(', ') || 'none';
      renderDrones(payload.atakDrones || []); renderFleetRoster(); refreshOpenModal(); drawFallback(payload.atakDrones || []);
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
            state.droneMarkers[drone.nodeId].addListener('click', () => openDroneModal(state.latestDrones[drone.nodeId] || drone, false));
            state.droneMarkers[drone.nodeId].addListener('mouseover', () => openDroneModal(state.latestDrones[drone.nodeId] || drone, false));
          }
          state.droneMarkers[drone.nodeId].setPosition(pos);
          state.droneMarkers[drone.nodeId].setIcon(markerIcon);
        }
      }
      if (state.googleReady && state.map) for (const [id, marker] of Object.entries(state.droneMarkers)) if (!seen.has(id)) { marker.setMap(null); delete state.droneMarkers[id]; }
    }
    function openDroneModal(drone, autoOpened) { state.selectedDroneId = drone.nodeId; $('droneModal').classList.add('open'); $('droneModal').setAttribute('aria-hidden', 'false'); renderDroneModal(drone, autoOpened); updateStreetView(drone); }
    function closeDroneModal() { $('droneModal').classList.remove('open'); $('droneModal').setAttribute('aria-hidden', 'true'); state.selectedDroneId = null; if (state.streetPanorama) state.streetPanorama.setVisible(false); }
    function refreshOpenModal() { if (state.selectedDroneId && state.latestDrones[state.selectedDroneId]) renderDroneModal(state.latestDrones[state.selectedDroneId], false); }
    function renderDroneModal(drone, autoOpened) {
      $('modalTitle').textContent = `${drone.nodeId} live view`;
      $('modalStatus').textContent = 'Simulated drone parameters.';
      const values = [['State', drone.state], ['Mission', drone.missionId || 'none'], ['Latitude', Number(drone.lat).toFixed(7)], ['Longitude', Number(drone.lon).toFixed(7)], ['Altitude', `${Number(drone.alt).toFixed(1)} m`], ['Battery', `${Number(drone.batteryPercent).toFixed(1)}%`], ['Source', drone.source], ['UID', drone.uid], ['Live exec', String(drone.liveExecution)], ['Last seen', drone.lastSeenIso || 'n/a']];
      $('paramGrid').innerHTML = values.map(([k, v]) => `<div class="param"><span>${k}</span><span>${v}</span></div>`).join('');
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
      const route = state.route.length ? state.route : window.DRONEOPS_CONFIG.defaultRoute; const all = [...route, ...drones.map(d => ({ lat: d.lat, lon: d.lon }))];
      const lats = all.map(p => Number(p.lat)); const lons = all.map(p => Number(p.lon)); const bounds = { minLat: Math.min(...lats) - .001, maxLat: Math.max(...lats) + .001, minLon: Math.min(...lons) - .001, maxLon: Math.max(...lons) + .001 };
      const rect = { x: 50, y: 50, width: canvas.width - 100, height: canvas.height - 100 }; const project = p => ({ x: rect.x + ((Number(p.lon) - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * rect.width, y: rect.y + rect.height - ((Number(p.lat) - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * rect.height });
      ctx.lineWidth = 5;
      for (let i = 0; i < route.length - 1; i++) { const a = project(route[i]); const b = project(route[i + 1]); ctx.strokeStyle = waypointColor(i + 1, route.length); ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
      route.forEach((point, i) => { const p = project(point); ctx.fillStyle = waypointColor(i, route.length); ctx.strokeStyle = '#eef4f8'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(p.x, p.y, 8, 0, Math.PI * 2); ctx.fill(); ctx.stroke(); ctx.fillStyle = '#071015'; ctx.font = '700 10px Arial'; ctx.textAlign = 'center'; ctx.fillText(String(i + 1), p.x, p.y + 3); });
      drones.forEach(drone => { const p = project({ lat: drone.lat, lon: drone.lon }); const identity = droneIdentity(drone.nodeId); drawCanvasDrone(ctx, p.x, p.y, identity, droneNumber(drone.nodeId)); ctx.fillStyle = '#eef4f8'; ctx.font = '12px Arial'; ctx.textAlign = 'left'; ctx.fillText(drone.nodeId, p.x + 14, p.y + 4); });
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
    $('startBtn').addEventListener('click', startMission); $('sendSelectedBtn').addEventListener('click', startMission);
    $('selectAllBtn').addEventListener('click', () => { state.selectedNodeIds = new Set(fleetIds()); renderFleetRoster(); });
    $('nodes').addEventListener('change', () => { const ids = new Set(fleetIds()); state.selectedNodeIds = new Set([...state.selectedNodeIds].filter(id => ids.has(id))); renderFleetRoster(); });
    $('addWaypointBtn').addEventListener('click', () => { const last = state.route[state.route.length - 1] || window.DRONEOPS_CONFIG.defaultRoute[0]; addWaypoint({ lat: Number(last.lat) + 0.001, lon: Number(last.lon) + 0.001, alt: Number(last.alt || 80) }); });
    $('resetRouteBtn').addEventListener('click', () => setRoute(window.DRONEOPS_CONFIG.defaultRoute));
    $('clearRouteBtn').addEventListener('click', () => setRoute([]));
    $('drawModeBtn').addEventListener('click', () => { state.drawMode = !state.drawMode; $('drawModeBtn').textContent = state.drawMode ? 'Drawing On' : 'Drawing Off'; $('drawModeBtn').className = state.drawMode ? 'small' : 'secondary small'; });
    $('holdBtn').addEventListener('click', () => issueLiveOrder('hold')); $('resumeBtn').addEventListener('click', () => issueLiveOrder('resume')); $('returnBtn').addEventListener('click', () => issueLiveOrder('return_to_start'));
    $('closeModalBtn').addEventListener('click', closeDroneModal); window.addEventListener('resize', () => drawFallback(Object.values(state.latestDrones)));
    renderFleetRoster(); renderWaypointEditor(); loadMap();
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
