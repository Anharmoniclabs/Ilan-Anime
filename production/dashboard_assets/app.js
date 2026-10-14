"use strict";

const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
const label = (value) => String(value || "unknown").replaceAll("_", " ").replaceAll("-", " ");
const badge = (value) => `<span class="badge ${esc(String(value).toLowerCase().replaceAll("_", "-"))}">${esc(label(value))}</span>`;

function renderMetrics(data) {
  const episode = data.episode;
  $("#shot-count").textContent = episode.shot_count;
  $("#shot-detail").textContent = `${Number(episode.body_frames).toLocaleString()} frames · ${episode.fps} fps`;
  const percent = episode.shot_count ? Math.round((episode.keyframe_covered_shots / episode.shot_count) * 100) : 0;
  $("#coverage").textContent = `${percent}%`;
  $("#rejected-motion").textContent = episode.animation_counts.rejected_motion_test || 0;
  $("#role-count").textContent = data.roles.count;
  $("#paused-count").textContent = data.runs.paused_count;
  $("#approval-count").textContent = data.runs.approvals.length;
  $("#truth").innerHTML = `<p class="eyebrow">PRODUCTION TRUTH</p><h2>${esc(data.truth_notice)}</h2><p>${esc(data.author_approval)}</p>`;
}

function renderBars(data) {
  const values = [
    ["Keyframe-covered shots", data.episode.keyframe_covered_shots, data.episode.shot_count, "amber"],
    ["Shots missing keyframes", data.episode.missing_keyframe_count, data.episode.shot_count, "steel"],
    ["Voice not recorded", data.episode.voice_counts.not_recorded || 0, data.episode.shot_count, "red"]
  ];
  $("#coverage-bars").innerHTML = values.map(([name, count, total, tone]) => {
    const width = total ? Math.round(count / total * 100) : 0;
    return `<div class="bar-row"><div><span>${esc(name)}</span><strong>${count}/${total}</strong></div><div class="bar"><i class="${tone}" style="width:${width}%"></i></div></div>`;
  }).join("");
}

function renderShots(shots, query = "") {
  const term = query.trim().toLowerCase();
  const filtered = shots.filter((shot) => Object.values(shot).join(" ").toLowerCase().includes(term));
  $("#shot-rows").innerHTML = filtered.map((shot) => `<tr>
    <td><strong>${esc(shot.id)}</strong></td><td>${shot.frames}</td><td>${badge(shot.status)}</td>
    <td>${badge(shot.animation_status)}</td><td>${badge(shot.voice_status)}</td><td>${shot.keyframes}</td>
  </tr>`).join("") || `<tr><td colspan="6" class="empty">No shots match this filter.</td></tr>`;
}

function renderRuns(data) {
  const paused = data.runs.runs.filter((run) => run.paused);
  $("#pause-notices").innerHTML = paused.map((run) => `<article class="pause"><strong>${esc(run.id)} is paused.</strong><p>${esc(run.pause_reason || "No reason recorded")}</p><small>It must not resume automatically.</small></article>`).join("");
  $("#run-cards").innerHTML = data.runs.runs.map((run) => `<article class="run-card">
    <header><div><p class="eyebrow">RUN</p><h3>${esc(run.id)}</h3></div>${badge(run.paused ? "paused" : "active")}</header>
    <p>${run.task_count} task${run.task_count === 1 ? "" : "s"} · ${run.open_task_count} open</p>
    <div class="task-list">${run.tasks.map((task) => `<div class="task"><div><strong>${esc(task.id)}</strong>${badge(task.state)}</div><p>${esc(task.role)} · ${esc((task.shots || []).join(", ") || "No shot IDs")}</p><small>${esc(task.objective)}</small></div>`).join("") || '<p class="empty">No tasks recorded.</p>'}</div>
  </article>`).join("") || '<p class="empty">No production runs recorded.</p>';
}

function renderAssets(data) {
  const counts = data.assets.counts;
  const preferred = ["canonical", "author-approved", "technical-approved", "submitted", "exploratory", "rejected", "partial", "unreviewed"];
  const states = [...preferred.filter((state) => Object.hasOwn(counts, state)), ...Object.keys(counts).filter((state) => !preferred.includes(state))];
  $("#asset-summary").innerHTML = states.map((state) => `<div><strong>${counts[state] || 0}</strong><span>${esc(label(state))}</span></div>`).join("") || '<p class="empty">No registered assets.</p>';
  $("#asset-cards").innerHTML = data.assets.items.map((asset) => `<article>
    <div><strong>${esc(asset.id)}${asset.version ? ` · v${asset.version}` : ""}</strong>${badge(asset.state)}</div>
    <p>${esc(asset.kind)} · ${esc(asset.mode)}${asset.shots.length ? ` · ${esc(asset.shots.join(", "))}` : ""}</p>
    <small>${esc(asset.path)}</small>
    ${asset.sha256 ? `<small class="hash">SHA-256 ${esc(asset.sha256)}</small>` : ""}
    ${asset.final_uses.length ? `<small class="final-use">Final use: ${esc(asset.final_uses.join(", "))}</small>` : ""}
  </article>`).join("") || '<p class="empty">No asset registry records found.</p>';
}

function renderRoles(data) {
  $("#role-cards").innerHTML = data.roles.roles.map((role) => `<article>
    <p class="eyebrow">${esc(role.id)}</p><h3>${esc(role.name)}</h3><p>${esc(role.duties)}</p>
    <footer><span>Reviewed by</span><strong>${esc(label(role.reviewer))}</strong></footer>
  </article>`).join("");
}

function wireTabs() {
  document.querySelectorAll(".tabs button").forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach((item) => { item.classList.remove("active"); item.setAttribute("aria-selected", "false"); });
    document.querySelectorAll(".panel").forEach((panel) => { panel.classList.remove("active"); panel.hidden = true; });
    button.classList.add("active"); button.setAttribute("aria-selected", "true");
    const panel = document.getElementById(button.dataset.panel); panel.hidden = false; panel.classList.add("active");
  }));
}

async function init() {
  wireTabs();
  try {
    const response = await fetch("/api/studio", {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    renderMetrics(data); renderBars(data); renderShots(data.episode.shots); renderRuns(data); renderAssets(data); renderRoles(data);
    $("#shot-filter").addEventListener("input", (event) => renderShots(data.episode.shots, event.target.value));
    if (data.errors.length) {
      $("#errors").hidden = false;
      $("#errors ul").innerHTML = data.errors.map((error) => `<li>${esc(error)}</li>`).join("");
    }
  } catch (error) {
    $("#truth").innerHTML = `<p class="eyebrow">DASHBOARD ERROR</p><h2>Production records could not be loaded.</h2><p>${esc(error.message)}</p>`;
  }
}

init();
