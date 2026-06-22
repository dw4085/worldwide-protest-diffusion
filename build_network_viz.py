#!/usr/bin/env python3
"""Build an interactive HTML network visualization from Model 2 coefficients CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from movement_categories import CATEGORIES

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Protest Diffusion Network — Model 2</title>
  <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
  <style>
    :root {
      --bg: #f6f4ef;
      --panel: #ffffff;
      --ink: #1f2933;
      --muted: #5d6b78;
      --positive: #1f7a4d;
      --negative: #b42318;
      --node: #2f4a68;
      --node-hover: #17324d;
      --border: #d8dde3;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(47, 74, 104, 0.08), transparent 28rem),
        var(--bg);
    }

    .page {
      max-width: 1400px;
      margin: 0 auto;
      padding: 24px;
    }

    .nav {
      margin-bottom: 18px;
      font-size: 0.95rem;
    }

    .nav a {
      color: var(--node);
    }

    h1 {
      margin: 0 0 8px;
      font-size: 1.9rem;
      font-weight: 600;
      letter-spacing: -0.02em;
    }

    .subtitle, .note, .interactive-guide {
      color: var(--muted);
      line-height: 1.5;
      max-width: 920px;
    }

    .interactive-guide {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px 18px;
      margin: 16px 0 4px;
      box-shadow: 0 8px 24px rgba(31, 41, 51, 0.04);
    }

    .interactive-guide h2 {
      margin: 0 0 10px;
      font-size: 1.05rem;
      color: var(--ink);
    }

    .interactive-guide ul {
      margin: 0;
      padding-left: 18px;
    }

    .interactive-guide li {
      margin-bottom: 6px;
    }

    .interactive-guide li:last-child {
      margin-bottom: 0;
    }

    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 12px 20px;
      align-items: center;
      margin: 20px 0 16px;
    }

    .control-group {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }

    .controls label {
      font-size: 0.95rem;
      color: var(--muted);
      margin-right: 4px;
    }

    .btn-group {
      display: inline-flex;
      border: 1px solid var(--border);
      border-radius: 999px;
      overflow: hidden;
      background: var(--panel);
    }

    .btn-group button {
      border: 0;
      background: transparent;
      padding: 10px 16px;
      cursor: pointer;
      font: inherit;
      color: var(--ink);
    }

    .btn-group button.active {
      background: var(--node);
      color: white;
    }

    .action-btn {
      border: 1px solid var(--border);
      border-radius: 999px;
      background: var(--panel);
      padding: 10px 16px;
      cursor: pointer;
      font: inherit;
      color: var(--ink);
    }

    .action-btn:hover {
      background: var(--node);
      color: white;
    }

    .sidebar .interpretation {
      margin-top: 18px;
      padding-top: 16px;
      border-top: 1px solid var(--border);
    }

    .sidebar .interpretation h2 {
      margin: 0 0 10px;
      font-size: 1.1rem;
    }

    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 320px;
      gap: 16px;
    }

    @media (max-width: 1100px) {
      .layout { grid-template-columns: 1fr; }
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: 0 10px 30px rgba(31, 41, 51, 0.06);
    }

    #chart-wrap {
      min-height: 760px;
      position: relative;
      overflow: hidden;
    }

    .zoom-controls {
      position: absolute;
      top: 14px;
      right: 14px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      z-index: 4;
    }

    .zoom-controls button {
      width: 40px;
      height: 40px;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.95);
      color: var(--ink);
      font-size: 1.15rem;
      line-height: 1;
      cursor: pointer;
      box-shadow: 0 4px 14px rgba(31, 41, 51, 0.08);
    }

    .zoom-controls button:hover {
      background: var(--node);
      color: white;
    }

    .zoom-controls #zoom-fit {
      font-size: 0.72rem;
      font-weight: 600;
      letter-spacing: 0.02em;
    }

    svg {
      width: 100%;
      height: 760px;
      display: block;
    }

    .sidebar {
      padding: 18px 18px 20px;
      min-height: 760px;
    }

    .sidebar h2 {
      margin: 0 0 10px;
      font-size: 1.1rem;
    }

    .sidebar p, .sidebar li {
      font-size: 0.95rem;
      line-height: 1.45;
      color: var(--muted);
    }

    .sidebar ul {
      padding-left: 18px;
      margin: 10px 0 0;
    }

    #detail {
      margin-top: 18px;
      padding-top: 16px;
      border-top: 1px solid var(--border);
      min-height: 220px;
    }

    #detail h3 {
      margin: 0 0 8px;
      font-size: 1rem;
      color: var(--ink);
    }

    #detail .empty {
      color: var(--muted);
      font-style: italic;
    }

    .tie-row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      padding: 6px 0;
      border-bottom: 1px solid rgba(216, 221, 227, 0.7);
      font-size: 0.92rem;
    }

    .tie-row:last-child { border-bottom: 0; }

    .pos { color: var(--positive); font-weight: 600; }
    .neg { color: var(--negative); font-weight: 600; }

    .legend {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      margin-top: 12px;
      font-size: 0.9rem;
      color: var(--muted);
    }

    .legend span::before {
      content: "";
      display: inline-block;
      width: 28px;
      height: 3px;
      margin-right: 8px;
      vertical-align: middle;
      border-radius: 999px;
    }

    .legend .pos-line::before { background: var(--positive); }
    .legend .neg-line::before { background: var(--negative); }

    .node circle {
      stroke: #fff;
      stroke-width: 2px;
      cursor: grab;
      transition: fill-opacity 160ms ease, stroke-width 160ms ease, stroke 160ms ease;
    }

    .node.selected circle {
      stroke: #f4b942;
      stroke-width: 3.5px;
    }

    .node.highlighted circle {
      stroke-width: 2.5px;
    }

    .node:active circle {
      cursor: grabbing;
    }

    .node text {
      pointer-events: none;
      font-size: 11px;
      fill: var(--ink);
      text-anchor: middle;
      transition: fill-opacity 160ms ease;
    }

    .link {
      fill: none;
      cursor: pointer;
      transition: stroke-opacity 160ms ease, stroke-width 160ms ease;
    }

    .tooltip {
      position: absolute;
      pointer-events: none;
      background: rgba(23, 50, 77, 0.94);
      color: #fff;
      padding: 8px 10px;
      border-radius: 8px;
      font-size: 12px;
      line-height: 1.35;
      max-width: 280px;
      opacity: 0;
      transition: opacity 120ms ease;
      z-index: 5;
    }
  </style>
</head>
<body>
  <div class="page">
    <p class="nav"><a href="protest_influence_summary.html">View influence summary ranking →</a></p>
    <h1>Protest Diffusion Network</h1>
    <p class="subtitle">
      Directed ties show lagged cross-category associations from Model 2 PPML regressions.
      Edge direction runs from the source movement category to the dependent movement category.
    </p>
    <p class="note">
      <strong>Note:</strong> Node positions combine tie-strength forces with a centrality layout:
      categories that send more, stronger positive outgoing ties are pulled toward the center.
      Coefficients are rescaled within the current filter for layout forces; hovers show actual values.
    </p>

    <section class="interactive-guide" aria-label="Interactive controls guide">
      <h2>Interactive controls</h2>
      <ul>
        <li><strong>Significance filter</strong> — Choose which ties appear using p &lt; 0.05, p &lt; 0.01, or p &lt; 0.001.</li>
        <li><strong>Tie direction filter</strong> — Show all ties, only positive ties (green), or only negative ties (red).</li>
        <li><strong>Reset layout</strong> — Discard manual drags and rerun the default force-directed layout for the current filters.</li>
        <li><strong>Zoom buttons</strong> — Use +, −, and Fit (top-right of the chart) to zoom in, zoom out, or refit the network to the window.</li>
        <li><strong>Pan and scroll zoom</strong> — Drag on empty chart space to pan; use the mouse wheel or trackpad to zoom.</li>
        <li><strong>Hover nodes or ties</strong> — See a tooltip with coefficient details; the sidebar shows the selected node or edge.</li>
        <li><strong>Click a node</strong> — Highlight that node, its neighbors, and connecting ties while fading everything else. Click the same node again or click the chart background to clear.</li>
        <li><strong>Drag a node</strong> — Reposition it manually; connected ties update in real time.</li>
      </ul>
    </section>

    <div class="controls">
      <div class="control-group">
        <label for="sig-buttons">Show ties significant at:</label>
        <div class="btn-group" id="sig-buttons">
          <button data-level="sig_05" class="active" type="button">p &lt; 0.05</button>
          <button data-level="sig_01" type="button">p &lt; 0.01</button>
          <button data-level="sig_001" type="button">p &lt; 0.001</button>
        </div>
      </div>
      <div class="control-group">
        <label for="sign-buttons">Show tie direction:</label>
        <div class="btn-group" id="sign-buttons">
          <button data-sign="all" class="active" type="button">All ties</button>
          <button data-sign="positive" type="button">Positive only</button>
          <button data-sign="negative" type="button">Negative only</button>
        </div>
      </div>
      <button id="reset-layout" class="action-btn" type="button">Reset layout</button>
    </div>

    <div class="layout">
      <div id="chart-wrap" class="panel">
        <div class="zoom-controls" aria-label="Zoom controls">
          <button id="zoom-in" type="button" title="Zoom in">+</button>
          <button id="zoom-out" type="button" title="Zoom out">−</button>
          <button id="zoom-fit" type="button" title="Fit network to window">Fit</button>
        </div>
        <div class="tooltip" id="tooltip"></div>
        <svg id="network" aria-label="Protest diffusion network"></svg>
      </div>
      <aside class="panel sidebar">
        <h2>How to read this</h2>
        <ul>
          <li>Each node is a movement category.</li>
          <li>Each arrow is a statistically significant lagged association in Model 2.</li>
          <li>Arrow direction runs from the <em>source</em> category (lagged predictor) to the <em>target</em> category (dependent protest type).</li>
          <li>Green arcs indicate positive coefficients; red arcs indicate negative coefficients.</li>
          <li>Line thickness and arrow size reflect the scaled strength of each tie.</li>
          <li>Click a node to highlight it, its neighbors, and their ties; click the background to clear.</li>
          <li>Drag any node to rearrange the layout manually.</li>
        </ul>
        <div class="legend">
          <span class="pos-line">Positive tie</span>
          <span class="neg-line">Negative tie</span>
        </div>
        <div class="interpretation">
          <h2>Layout &amp; interpretation</h2>
          <p>
            The network uses a force-directed layout shaped by source centrality. For the ties
            currently shown, each node receives a score based on how many outgoing ties it sends
            and how strong its outgoing <em>positive</em> ties are (both rescaled to [−1, 1] for
            forces). Nodes with more, stronger positive outgoing ties are pulled toward the center;
            peripheral nodes send fewer or weaker positive ties.
          </p>
          <ul>
            <li><strong>Positive ties</strong> act like springs with shorter target distances, pulling categories together.</li>
            <li><strong>Negative ties</strong> act like springs with longer target distances, pushing categories apart.</li>
            <li><strong>Central placement</strong> highlights categories that positively predict many other movement types in the current view.</li>
            <li><strong>Thicker, larger arrows</strong> indicate stronger associations among the ties currently shown.</li>
            <li><strong>Clusters</strong> suggest movement categories linked by multiple positive associations in the current view.</li>
            <li><strong>Proximity is suggestive, not proof.</strong> Shared ties, drag adjustments, and the global layout all shape positions; read arrows and coefficients directly for inference.</li>
          </ul>
          <p>
            Use <strong>Reset layout</strong> to discard manual drags and rerun the default layout for the current filters.
          </p>
        </div>
        <div id="detail">
          <h3>Selection</h3>
          <div class="empty">Click a node to highlight its neighborhood, or hover to inspect coefficients.</div>
        </div>
      </aside>
    </div>
  </div>

  <script>
    const DATA = __DATA_JSON__;
    const CATEGORIES = __CATEGORIES_JSON__;

    const svg = d3.select("#network");
    const wrap = d3.select("#chart-wrap");
    const tooltip = d3.select("#tooltip");
    const detail = d3.select("#detail");

    let width = 0;
    let height = 760;
    let currentLevel = "sig_05";
    let currentSignFilter = "all";
    let simulation = null;
    let currentNodes = [];
    let graphState = null;
    let selectedNodeId = null;
    const NODE_RADIUS = 18;
    const ARROW_BUCKETS = 5;

    const g = svg.append("g");
    const defs = svg.append("defs");

    function createWeightedMarkers() {
      defs.selectAll("marker.weighted-arrow").remove();

      for (let bucket = 1; bucket <= ARROW_BUCKETS; bucket += 1) {
        const weight = bucket / ARROW_BUCKETS;
        const size = 5 + weight * 10;
        const halfHeight = size * 0.45;

        [
          ["positive", "#1f7a4d"],
          ["negative", "#b42318"],
        ].forEach(([kind, color]) => {
          [
            ["", 1],
            ["-faded", 0.07],
          ].forEach(([suffix, opacity]) => {
            defs.append("marker")
              .attr("class", "weighted-arrow")
              .attr("id", `arrow-${kind}-${bucket}${suffix}`)
              .attr("viewBox", `0 ${-halfHeight} ${size} ${halfHeight * 2}`)
              .attr("refX", size)
              .attr("refY", 0)
              .attr("markerWidth", size)
              .attr("markerHeight", size)
              .attr("markerUnits", "userSpaceOnUse")
              .attr("orient", "auto")
              .append("path")
              .attr("d", `M0,${-halfHeight} L${size},0 L0,${halfHeight} Z`)
              .attr("fill", color)
              .attr("fill-opacity", opacity);
          });
        });
      }
    }

    createWeightedMarkers();

    const linkLayer = g.append("g").attr("class", "links");
    const nodeLayer = g.append("g").attr("class", "nodes");

    const zoom = d3.zoom()
      .scaleExtent([0.05, 4])
      .on("zoom", (event) => g.attr("transform", event.transform));
    svg.call(zoom);

    function resize() {
      width = wrap.node().clientWidth;
      svg.attr("viewBox", [0, 0, width, height]);
      if (simulation) {
        simulation.force("center", d3.forceCenter(width / 2, height / 2));
      }
    }

    function highlightSets(nodeId, links) {
      if (!nodeId) {
        return { nodeIds: new Set(), linkKeys: new Set() };
      }

      const nodeIds = new Set([nodeId]);
      const linkKeys = new Set();

      links.forEach((link) => {
        if (link.source.id === nodeId || link.target.id === nodeId) {
          linkKeys.add(`${link.source.id}-${link.target.id}`);
          nodeIds.add(link.source.id);
          nodeIds.add(link.target.id);
        }
      });

      return { nodeIds, linkKeys };
    }

    function clearSelectionDetail() {
      detail.html(`
        <h3>Selection</h3>
        <div class="empty">Click a node to highlight its neighborhood, or hover to inspect coefficients.</div>
      `);
    }

    function applyHighlight() {
      if (!graphState) return;

      const { links, linkMerge, node } = graphState;
      const active = Boolean(selectedNodeId);
      const { nodeIds, linkKeys } = highlightSets(selectedNodeId, links);

      linkMerge
        .classed("highlighted", (d) =>
          active && linkKeys.has(`${d.source.id}-${d.target.id}`)
        )
        .classed("faded", (d) =>
          active && !linkKeys.has(`${d.source.id}-${d.target.id}`)
        )
        .attr("stroke-opacity", (d) => {
          const base = 0.35 + 0.55 * d.forceStrength;
          if (!active) return base;
          return linkKeys.has(`${d.source.id}-${d.target.id}`) ? base : 0.07;
        })
        .attr("stroke-width", (d) => {
          const base = 1.5 + 5 * d.forceStrength;
          if (!active) return base;
          return linkKeys.has(`${d.source.id}-${d.target.id}`) ? base + 0.75 : base;
        })
        .attr("marker-end", (d) => {
          if (!active) return markerUrl(d);
          const highlighted = linkKeys.has(`${d.source.id}-${d.target.id}`);
          return markerUrl(d, !highlighted);
        });

      node
        .classed("selected", (d) => active && d.id === selectedNodeId)
        .classed("highlighted", (d) =>
          active && nodeIds.has(d.id) && d.id !== selectedNodeId
        )
        .classed("faded", (d) => active && !nodeIds.has(d.id))
        .select("circle")
        .attr("fill-opacity", (d) => {
          if (!active) return 1;
          return nodeIds.has(d.id) ? 1 : 0.1;
        });

      node.select("text").attr("fill-opacity", (d) => {
        if (!active) return 1;
        return nodeIds.has(d.id) ? 1 : 0.12;
      });
    }

    function selectNode(nodeData, links) {
      selectedNodeId = selectedNodeId === nodeData.id ? null : nodeData.id;
      applyHighlight();
      if (selectedNodeId) {
        nodeSummary(nodeData, links);
      } else {
        clearSelectionDetail();
      }
    }

    function assignSourceCentrality(nodes, links) {
      const stats = new Map(
        nodes.map((n) => [n.id, { outCount: 0, posWeight: 0 }])
      );

      links.forEach((link) => {
        const sourceStats = stats.get(link.source.id);
        sourceStats.outCount += 1;
        if (link.coefficient >= 0) {
          sourceStats.posWeight += link.forceStrength;
        }
      });

      const maxCount = d3.max(nodes, (n) => stats.get(n.id).outCount) || 1;
      const maxWeight = d3.max(nodes, (n) => stats.get(n.id).posWeight) || 1;
      const hasPositiveTies = links.some((link) => link.coefficient >= 0);

      nodes.forEach((node) => {
        const sourceStats = stats.get(node.id);
        const normCount = sourceStats.outCount / maxCount;
        const normWeight = maxWeight ? sourceStats.posWeight / maxWeight : 0;
        node.outCount = sourceStats.outCount;
        node.posOutWeight = sourceStats.posWeight;
        node.centrality = hasPositiveTies
          ? 0.45 * normCount + 0.55 * normWeight
          : normCount;
      });
    }

    function initializeNodePositions(nodes) {
      const cx = width / 2;
      const cy = height / 2;
      const spread = Math.min(width, height) * 0.46;

      nodes.forEach((node, index) => {
        const angle = (index / nodes.length) * 2 * Math.PI - Math.PI / 2;
        const ring = spread * (0.2 + 0.8 * (1 - (node.centrality || 0)));
        node.x = cx + ring * Math.cos(angle);
        node.y = cy + ring * Math.sin(angle);
      });
    }

    function fitToView(animate = true) {
      if (!width || !height) return;

      const padding = 28;
      let bounds = null;

      try {
        bounds = g.node().getBBox();
      } catch (error) {
        bounds = null;
      }

      if (
        !bounds ||
        !Number.isFinite(bounds.width) ||
        !Number.isFinite(bounds.height) ||
        bounds.width <= 0 ||
        bounds.height <= 0
      ) {
        if (!currentNodes.length) return;
        let minX = Infinity;
        let minY = Infinity;
        let maxX = -Infinity;
        let maxY = -Infinity;
        currentNodes.forEach((node) => {
          if (!Number.isFinite(node.x) || !Number.isFinite(node.y)) return;
          minX = Math.min(minX, node.x - 24);
          maxX = Math.max(maxX, node.x + 24);
          minY = Math.min(minY, node.y - 24);
          maxY = Math.max(maxY, node.y + 38);
        });
        if (!Number.isFinite(minX)) return;
        bounds = {
          x: minX,
          y: minY,
          width: Math.max(maxX - minX, 1),
          height: Math.max(maxY - minY, 1),
        };
      }

      const midX = bounds.x + bounds.width / 2;
      const midY = bounds.y + bounds.height / 2;
      const scale = Math.min(
        (width - padding * 2) / bounds.width,
        (height - padding * 2) / bounds.height
      ) * 0.98;

      if (!Number.isFinite(scale) || scale <= 0) return;

      const transform = d3.zoomIdentity
        .translate(width / 2, height / 2)
        .scale(scale)
        .translate(-midX, -midY);

      const transition = animate
        ? svg.transition().duration(350)
        : svg;
      transition.call(zoom.transform, transform);
    }

    function zoomBy(factor) {
      svg.transition().duration(200).call(zoom.scaleBy, factor);
    }

    function scaleCoefficients(links) {
      const maxAbs = d3.max(links, d => Math.abs(d.coefficient)) || 1;
      links.forEach(d => {
        d.scaled = d.coefficient / maxAbs;
        d.forceStrength = Math.abs(d.scaled);
      });
      return maxAbs;
    }

    function pairKey(sourceId, targetId) {
      return [sourceId, targetId].sort().join("|||");
    }

    function annotateBidirectional(links) {
      const counts = new Map();
      links.forEach(d => {
        const key = pairKey(d.source.id ?? d.source, d.target.id ?? d.target);
        counts.set(key, (counts.get(key) || 0) + 1);
      });

      const seen = new Map();
      links.forEach(d => {
        const sourceId = d.source.id ?? d.source;
        const targetId = d.target.id ?? d.target;
        const key = pairKey(sourceId, targetId);
        const bidirectional = counts.get(key) > 1;
        d.bidirectional = bidirectional;
        if (!bidirectional) {
          d.curve = 0.18;
          d.clockwise = 1;
          return;
        }
        const dirKey = `${sourceId}->${targetId}`;
        const index = seen.get(key) || 0;
        seen.set(key, index + 1);
        d.curve = 0.34;
        d.clockwise = sourceId < targetId ? 1 : 0;
        d.offsetIndex = index;
      });
    }

    function arrowBucket(forceStrength) {
      return Math.max(
        1,
        Math.min(ARROW_BUCKETS, Math.ceil(forceStrength * ARROW_BUCKETS))
      );
    }

    function markerUrl(link, faded = false) {
      const bucket = arrowBucket(link.forceStrength);
      const kind = link.coefficient >= 0 ? "positive" : "negative";
      const suffix = faded ? "-faded" : "";
      return `url(#arrow-${kind}-${bucket}${suffix})`;
    }

    function dragBehavior(simulation, linkSelection) {
      function dragstarted(event, d) {
        if (event.sourceEvent) event.sourceEvent.stopPropagation();
        if (!event.active) simulation.alphaTarget(0.12).restart();
        d.fx = d.x;
        d.fy = d.y;
        d3.select(this).raise();
      }

      function dragged(event, d) {
        const [x, y] = d3.pointer(event, g.node());
        d.fx = x;
        d.fy = y;
        linkSelection.attr("d", linkPath);
      }

      function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }

      return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
    }

    function linkPath(d) {
      const x1 = d.source.x;
      const y1 = d.source.y;
      const x2 = d.target.x;
      const y2 = d.target.y;
      const dx = x2 - x1;
      const dy = y2 - y1;
      const dist = Math.hypot(dx, dy) || 1;
      const ux = dx / dist;
      const uy = dy / dist;

      const sx = x1 + ux * NODE_RADIUS;
      const sy = y1 + uy * NODE_RADIUS;
      const tx = x2 - ux * NODE_RADIUS;
      const ty = y2 - uy * NODE_RADIUS;

      if (dist < NODE_RADIUS * 2.4) {
        return `M${sx},${sy}L${tx},${ty}`;
      }

      const dr = Math.max(dist * (1 + (d.curve || 0)), NODE_RADIUS * 2);
      const sweep = d.clockwise ? 1 : 0;
      return `M${sx},${sy}A${dr},${dr} 0 0,${sweep} ${tx},${ty}`;
    }

    function clampNodes(nodes, resetVelocity = false) {
      const cx = width / 2;
      const cy = height / 2;
      const maxRadius = Math.min(width, height) * 0.52;

      nodes.forEach((node) => {
        if (!Number.isFinite(node.x) || !Number.isFinite(node.y)) {
          node.x = cx;
          node.y = cy;
        }
        const dx = node.x - cx;
        const dy = node.y - cy;
        const radius = Math.hypot(dx, dy);
        if (radius > maxRadius) {
          node.x = cx + (dx / radius) * maxRadius;
          node.y = cy + (dy / radius) * maxRadius;
          if (resetVelocity) {
            node.vx = 0;
            node.vy = 0;
          }
        }
      });
    }

    function linkDistance(link) {
      const pull = 135 + 35 * (1 - link.forceStrength);
      const push = 180 + 50 * link.forceStrength;
      return link.coefficient >= 0 ? pull : push;
    }

    function linkStrength(link) {
      return 0.07 + 0.18 * link.forceStrength;
    }

    function runLayout(nodes, links, linkMerge, node) {
      if (simulation) simulation.stop();

      const cx = width / 2;
      const cy = height / 2;
      const maxRing = Math.min(width, height) * 0.44;

      simulation = d3.forceSimulation(nodes)
        .force(
          "link",
          d3.forceLink(links)
            .id((d) => d.id)
            .distance(linkDistance)
            .strength(linkStrength)
        )
        .force(
          "radial",
          d3.forceRadial(
            (d) => maxRing * (1 - (d.centrality || 0)),
            cx,
            cy
          ).strength((d) => 0.15 + 0.6 * (d.centrality || 0))
        )
        .force("charge", d3.forceManyBody().strength(-160))
        .force("center", d3.forceCenter(cx, cy).strength(0.02))
        .force("collision", d3.forceCollide(44))
        .alphaDecay(0.04)
        .velocityDecay(0.35);

      node.call(dragBehavior(simulation, linkMerge));

      simulation.on("tick", () => {
        clampNodes(nodes, false);
        linkMerge.attr("d", linkPath);
        node.attr("transform", (d) => `translate(${d.x},${d.y})`);
      });

      simulation.on("end", () => {
        clampNodes(nodes, true);
        linkMerge.attr("d", linkPath);
        node.attr("transform", (d) => `translate(${d.x},${d.y})`);
        applyHighlight();
        fitToView(true);
      });

      simulation.alpha(1).restart();
    }

    function filteredLinks(level, signFilter = currentSignFilter) {
      return DATA.links
        .filter((d) => d[level])
        .filter((d) => {
          if (signFilter === "positive") return d.coefficient >= 0;
          if (signFilter === "negative") return d.coefficient < 0;
          return true;
        })
        .map((d) => ({ ...d }));
    }

    function resetLayout() {
      if (!graphState) return;

      const { nodes, links, linkMerge, node } = graphState;
      nodes.forEach((n) => {
        n.fx = null;
        n.fy = null;
        n.vx = 0;
        n.vy = 0;
      });
      assignSourceCentrality(nodes, links);
      initializeNodePositions(nodes);
      linkMerge.attr("d", linkPath);
      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
      runLayout(nodes, links, linkMerge, node);
    }

    function nodeSummary(node, links) {
      const outgoing = links.filter(l => (l.source.id ?? l.source) === node.id);
      const incoming = links.filter(l => (l.target.id ?? l.target) === node.id);
      const rows = [];

      outgoing.forEach(l => {
        rows.push({
          label: `${node.label} → ${l.target.label}`,
          value: l.coefficient,
          stars: l.stars
        });
      });
      incoming.forEach(l => {
        rows.push({
          label: `${l.source.label} → ${node.label}`,
          value: l.coefficient,
          stars: l.stars
        });
      });

      rows.sort((a, b) => Math.abs(b.value) - Math.abs(a.value));

      detail.html(`<h3>${node.label}</h3>`);
      if (!rows.length) {
        detail.append("div").attr("class", "empty").text("No significant ties match the current filters.");
        return;
      }
      const list = detail.append("div");
      rows.forEach(row => {
        const cls = row.value >= 0 ? "pos" : "neg";
        list.append("div")
          .attr("class", "tie-row")
          .html(`<span>${row.label}</span><span class="${cls}">${row.value.toExponential(3)}${row.stars}</span>`);
      });
    }

    function edgeSummary(link) {
      const cls = link.coefficient >= 0 ? "pos" : "neg";
      detail.html(`
        <h3>${link.source.label} → ${link.target.label}</h3>
        <div class="tie-row">
          <span>Actual coefficient</span>
          <span class="${cls}">${link.coefficient.toExponential(6)}${link.stars}</span>
        </div>
        <div class="tie-row">
          <span>t-statistic</span>
          <span>${link.t_stat.toFixed(2)}</span>
        </div>
        <div class="tie-row">
          <span>Scaled force weight</span>
          <span>${link.scaled.toFixed(4)}</span>
        </div>
      `);
    }

    function showTooltip(html, event) {
      const bounds = wrap.node().getBoundingClientRect();
      tooltip
        .style("opacity", 1)
        .style("left", `${event.clientX - bounds.left + 14}px`)
        .style("top", `${event.clientY - bounds.top + 14}px`)
        .html(html);
    }

    function hideTooltip() {
      tooltip.style("opacity", 0);
    }

    function render() {
      resize();
      svg.call(zoom.transform, d3.zoomIdentity);
      const previousSelection = selectedNodeId;

      const linksRaw = filteredLinks(currentLevel);
      scaleCoefficients(linksRaw);

      const nodes = CATEGORIES.map((d) => ({ ...d }));
      currentNodes = nodes;
      const nodeById = new Map(nodes.map((d) => [d.id, d]));
      const links = linksRaw.map((d) => ({
        ...d,
        source: nodeById.get(d.source),
        target: nodeById.get(d.target),
      }));

      selectedNodeId = previousSelection && nodeById.has(previousSelection)
        ? previousSelection
        : null;

      annotateBidirectional(links);
      assignSourceCentrality(nodes, links);
      initializeNodePositions(nodes);

      const link = linkLayer.selectAll("path.link")
        .data(links, (d) => `${d.source.id}-${d.target.id}`);

      link.exit().remove();

      const linkEnter = link.enter()
        .append("path")
        .attr("class", "link")
        .attr("fill", "none")
        .on("mousemove", (event, d) => {
          showTooltip(
            `<strong>${d.source.label} → ${d.target.label}</strong><br/>
             coef: ${d.coefficient.toExponential(6)}${d.stars}<br/>
             scaled: ${d.scaled.toFixed(4)}`,
            event
          );
          edgeSummary(d);
        })
        .on("mouseleave", hideTooltip);

      const linkMerge = linkEnter.merge(link);
      linkMerge
        .attr("stroke", (d) => (d.coefficient >= 0 ? "#1f7a4d" : "#b42318"))
        .attr("stroke-opacity", (d) => 0.35 + 0.55 * d.forceStrength)
        .attr("stroke-width", (d) => 1.5 + 5 * d.forceStrength)
        .attr("marker-end", (d) => markerUrl(d));

      const node = nodeLayer.selectAll("g.node")
        .data(nodes, (d) => d.id)
        .join((enter) => {
          const ng = enter.append("g").attr("class", "node");
          ng.append("circle").attr("r", 16);
          ng.append("text").attr("dy", 34);
          return ng;
        });

      node
        .select("circle")
        .attr("fill", "#2f4a68")
        .on("mousemove", (event, d) => {
          const activeLinks = links.filter(
            (l) => l.source.id === d.id || l.target.id === d.id
          );
          showTooltip(
            `<strong>${d.label}</strong><br/>
             ${activeLinks.length} significant ties<br/>
             Outgoing ties: ${d.outCount}<br/>
             Source centrality: ${((d.centrality || 0) * 100).toFixed(0)}%`,
            event
          );
          if (!selectedNodeId) {
            nodeSummary(d, links);
          }
        })
        .on("mouseleave", hideTooltip);

      node
        .on("click", (event, d) => {
          event.stopPropagation();
          selectNode(d, links);
        });

      node.select("text").text((d) => d.short);

      linkMerge.attr("d", linkPath);
      node.attr("transform", (d) => `translate(${d.x},${d.y})`);

      graphState = { nodes, links, linkMerge, node };
      applyHighlight();
      if (selectedNodeId) {
        nodeSummary(nodeById.get(selectedNodeId), links);
      }
      runLayout(nodes, links, linkMerge, node);
    }

    svg.on("click", () => {
      if (!selectedNodeId) return;
      selectedNodeId = null;
      applyHighlight();
      clearSelectionDetail();
    });

    d3.select("#zoom-in").on("click", () => zoomBy(1.28));
    d3.select("#zoom-out").on("click", () => zoomBy(1 / 1.28));
    d3.select("#zoom-fit").on("click", () => fitToView(true));
    d3.select("#reset-layout").on("click", () => resetLayout());

    d3.selectAll("#sig-buttons button").on("click", function() {
      d3.selectAll("#sig-buttons button").classed("active", false);
      d3.select(this).classed("active", true);
      currentLevel = this.dataset.level;
      render();
    });

    d3.selectAll("#sign-buttons button").on("click", function() {
      d3.selectAll("#sign-buttons button").classed("active", false);
      d3.select(this).classed("active", true);
      currentSignFilter = this.dataset.sign;
      render();
    });

    window.addEventListener("resize", () => {
      resize();
      if (currentNodes.length) {
        fitToView(false);
      }
    });

    requestAnimationFrame(() => {
      render();
    });
  </script>
</body>
</html>
"""


def short_label(title: str) -> str:
    replacements = {
        "Governance & Politics": "Governance",
        "Human Rights & Identity": "Human Rights",
        "Justice & Accountability": "Justice",
        "Security & Conflict": "Security",
        "Health & Social Welfare": "Health",
        "Religion & Belief": "Religion",
        "Prices & Economy": "Economy",
        "Public Services & Infrastructure": "Public Services",
        "International Solidarity & Foreign Policy": "Intl Solidarity",
        "Agriculture & Rural": "Agriculture",
        "Land, Property & Housing": "Land & Housing",
    }
    return replacements.get(title, title)


def load_csv(csv_path: Path) -> list[dict[str, object]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_payload(rows: list[dict[str, object]]) -> dict[str, object]:
    nodes = [
        {
            "id": base,
            "label": title,
            "short": short_label(title),
        }
        for title, base in CATEGORIES
    ]

    links = []
    for row in rows:
        links.append(
            {
                "source": next(base for title, base in CATEGORIES if title == row["source_category"]),
                "target": next(base for title, base in CATEGORIES if title == row["target_category"]),
                "source_label": row["source_category"],
                "target_label": row["target_category"],
                "coefficient": float(row["coefficient"]),
                "t_stat": float(row["t_stat"]),
                "stars": row["stars"],
                "sig_05": row["sig_05"] == "True",
                "sig_01": row["sig_01"] == "True",
                "sig_001": row["sig_001"] == "True",
            }
        )

    return {"nodes": nodes, "links": links}


def render_html(payload: dict[str, object]) -> str:
    categories = payload["nodes"]
    data = {"links": payload["links"]}
    return (
        HTML_TEMPLATE.replace("__DATA_JSON__", json.dumps(data, indent=2))
        .replace("__CATEGORIES_JSON__", json.dumps(categories, indent=2))
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build an interactive HTML protest diffusion network from coefficients CSV."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("model2_coefficients.csv"),
        help="Input CSV produced by extract_coefficients.py",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("protest_diffusion_network.html"),
        help="Output HTML path",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Input CSV not found: {args.input}", file=sys.stderr)
        print("Run extract_coefficients.py first.", file=sys.stderr)
        return 1

    rows = load_csv(args.input)
    payload = build_payload(rows)
    html = render_html(payload)
    args.output.write_text(html, encoding="utf-8")
    print(f"Wrote visualization to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
