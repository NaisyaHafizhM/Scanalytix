/* Auto EDA Insight — stable compact sidebar rail.
   - The compact rail contains navigation icons only.
   - The single sidebar open control is Streamlit's native button in the header.
   - The dashboard expands to the remaining width.
   - No rapid polling or broad DOM observer is used, preventing sidebar lag.
   - The Streamlit top header auto-hides while the main page is scrolled so
     content is not covered by a frozen toolbar. */
(function () {
  "use strict";

  const cfg = window.PF_RAIL_CONFIG || {};
  const hostWindow = window.parent || window;
  const doc = hostWindow.document;
  if (!doc || !doc.body) return;

  const STATE_KEY = "__PF_COMPACT_RAIL_STATE__";
  const STYLE_ID = "pf-compact-rail-style";
  const RAIL_ID = "pf-compact-rail";
  const FLYOUT_ID = "pf-compact-rail-flyout";
  const BODY_CLASS = "pf-compact-rail-visible";
  const HEADER_HIDDEN_CLASS = "pf-header-auto-hidden";
  const NATIVE_HIDDEN_CLASS = "pf-native-sidebar-control-hidden";

  const previous = hostWindow[STATE_KEY];
  if (previous && typeof previous.destroy === "function") previous.destroy();

  const state = {
    destroyed: false,
    lastCollapsed: null,
    sidebar: null,
    sidebarObserver: null,
    sidebarResizeObserver: null,
    header: null,
    headerObserver: null,
    scrollTarget: null,
    rafId: null,
    timers: [],
    handlers: {},
    activeFlyout: null,
    destroy: null
  };
  hostWindow[STATE_KEY] = state;

  function removeNode(id) {
    const node = doc.getElementById(id);
    if (node) node.remove();
  }

  function later(fn, delay) {
    const id = hostWindow.setTimeout(() => {
      state.timers = state.timers.filter((value) => value !== id);
      if (!state.destroyed) fn();
    }, delay);
    state.timers.push(id);
    return id;
  }

  function scheduleSync() {
    if (state.destroyed || state.rafId !== null) return;
    state.rafId = hostWindow.requestAnimationFrame(() => {
      state.rafId = null;
      syncLayout();
    });
  }

  function normalize(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[\u{1F300}-\u{1FAFF}]/gu, "")
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  function sidebarElement() {
    return doc.querySelector('section[data-testid="stSidebar"]');
  }

  function isSidebarCollapsed(sidebar) {
    if (!sidebar) return state.lastCollapsed === true;

    const aria = sidebar.getAttribute("aria-expanded");
    if (aria === "false") return true;
    if (aria === "true") return false;

    const dataCollapsed = sidebar.getAttribute("data-collapsed");
    if (dataCollapsed === "true") return true;
    if (dataCollapsed === "false") return false;

    const rect = sidebar.getBoundingClientRect();
    const style = hostWindow.getComputedStyle(sidebar);
    const transform = style.transform || "none";

    return (
      rect.width < 8 ||
      rect.right <= 8 ||
      rect.left < -40 ||
      style.visibility === "hidden" ||
      style.display === "none" ||
      (transform !== "none" && rect.right < 48)
    );
  }

  function isNativeSidebarControl(button) {
    if (!button || !button.matches || !button.matches("button")) return false;
    if (button.closest(`#${RAIL_ID}`)) return false;
    if (button.closest('section[data-testid="stSidebar"]')) return false;

    const wrapper = button.closest(
      '[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapseButton"]'
    );
    if (wrapper) return true;

    const label = normalize(
      button.getAttribute("aria-label") ||
      button.getAttribute("title") ||
      button.textContent
    );
    if (
      label.includes("open sidebar") ||
      label.includes("show sidebar") ||
      label.includes("expand sidebar") ||
      label.includes("buka sidebar")
    ) return true;

    /* Streamlit has changed the aria-label/test-id of this control between
       releases.  When the sidebar is closed, the remaining left-most header
       button is still the native sidebar opener.  Detect it by position as a
       safe fallback, while leaving Deploy/menu controls on the right intact. */
    const header = button.closest('[data-testid="stHeader"]');
    if (header && button.querySelector("svg")) {
      const rect = button.getBoundingClientRect();
      const headerRect = header.getBoundingClientRect();
      if (rect.width > 0 && rect.width <= 140 && rect.left < headerRect.left + 190) {
        return true;
      }
    }
    return false;
  }

  function nativeSidebarControls() {
    const controls = new Set();

    doc.querySelectorAll(
      '[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapseButton"]'
    ).forEach((node) => {
      /* Ignore the normal close button that belongs to the expanded sidebar.
         Only the external opener must be hidden/reused in compact mode. */
      if (node.closest('section[data-testid="stSidebar"]')) return;
      controls.add(node);
      const button = node.matches("button") ? node : node.querySelector("button");
      if (button) controls.add(button);
    });

    doc.querySelectorAll("button").forEach((button) => {
      if (isNativeSidebarControl(button)) {
        controls.add(button);
        const wrapper = button.closest(
          '[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapseButton"]'
        );
        if (wrapper) controls.add(wrapper);
      }
    });

    return Array.from(controls);
  }

  function setNativeOpenControlsHidden(hidden) {
    nativeSidebarControls().forEach((node) => {
      node.classList.toggle(NATIVE_HIDDEN_CLASS, hidden);
      if (hidden) node.setAttribute("aria-hidden", "true");
      else node.removeAttribute("aria-hidden");
    });
  }

  function firstNativeOpenButton() {
    const nodes = nativeSidebarControls();
    for (const node of nodes) {
      if (node.matches && node.matches("button")) return node;
      const button = node.querySelector && node.querySelector("button");
      if (button) return button;
    }
    return null;
  }

  function findSidebarButton(target) {
    const sidebar = sidebarElement();
    if (!sidebar) return null;
    const wanted = normalize(target);
    return Array.from(sidebar.querySelectorAll("button")).find((button) => {
      const text = normalize(button.innerText || button.textContent || "");
      return text === wanted || text.endsWith(wanted) || text.includes(wanted);
    }) || null;
  }

  function navigateTo(target, group) {
    const button = findSidebarButton(target);
    if (button) {
      button.click();
      return;
    }

    const sidebar = sidebarElement();
    if (!sidebar) return;
    const wanted = normalize(group || target);
    const summary = Array.from(sidebar.querySelectorAll("summary")).find((node) => {
      const text = normalize(node.innerText || node.textContent || "");
      return text && (text === wanted || text.includes(wanted) || wanted.includes(text));
    });
    if (summary && !summary.closest("details")?.open) summary.click();
    later(() => {
      const retry = findSidebarButton(target);
      if (retry) retry.click();
    }, 90);
  }

  function openSidebar() {
    const button = firstNativeOpenButton();
    if (!button) return;

    /* Hide the compact rail immediately. The native sidebar then owns the
       same left edge, so there is no duplicated arrow or overlapping panel. */
    doc.body.classList.remove(BODY_CLASS);
    setNativeOpenControlsHidden(false);
    button.click();
    later(scheduleSync, 40);
    later(scheduleSync, 180);
    later(scheduleSync, 360);
  }

  function bindSidebar(sidebar) {
    if (!sidebar || sidebar === state.sidebar) return;

    if (state.sidebarObserver) state.sidebarObserver.disconnect();
    if (state.sidebarResizeObserver) state.sidebarResizeObserver.disconnect();

    state.sidebar = sidebar;
    state.sidebarObserver = new MutationObserver(scheduleSync);
    state.sidebarObserver.observe(sidebar, {
      attributes: true,
      attributeFilter: ["aria-expanded", "data-collapsed", "style", "class"]
    });

    if ("ResizeObserver" in hostWindow) {
      state.sidebarResizeObserver = new hostWindow.ResizeObserver(scheduleSync);
      state.sidebarResizeObserver.observe(sidebar);
    }

    sidebar.addEventListener("transitionend", scheduleSync, { passive: true });
  }

  function bindHeader() {
    const header = doc.querySelector('[data-testid="stHeader"]');
    if (!header || header === state.header) return;

    if (state.headerObserver) state.headerObserver.disconnect();
    state.header = header;
    /* Streamlit may mount its collapsed sidebar opener slightly after the
       sidebar transition.  Watching only the header's children is lightweight
       and lets us hide that late control immediately without polling. */
    state.headerObserver = new MutationObserver(scheduleSync);
    state.headerObserver.observe(header, { childList: true, subtree: true });
  }

  function getMainScrollTarget() {
    const candidates = [
      doc.querySelector('[data-testid="stAppViewContainer"] .main'),
      doc.querySelector('[data-testid="stMain"]'),
      doc.querySelector("section.main"),
      doc.querySelector("main")
    ].filter(Boolean);

    return candidates.find((node) => {
      const style = hostWindow.getComputedStyle(node);
      return /(auto|scroll)/.test(style.overflowY || "") || node.scrollHeight > node.clientHeight + 8;
    }) || candidates[0] || hostWindow;
  }

  function updateHeaderOnScroll() {
    if (state.destroyed) return;
    const target = state.scrollTarget;
    const top = target === hostWindow
      ? (hostWindow.scrollY || doc.documentElement.scrollTop || 0)
      : (target ? target.scrollTop : 0);
    doc.body.classList.toggle(HEADER_HIDDEN_CLASS, top > 12);
  }

  function bindScrollTarget() {
    const target = getMainScrollTarget();
    if (!target || target === state.scrollTarget) return;

    if (state.scrollTarget && state.handlers.scroll) {
      state.scrollTarget.removeEventListener("scroll", state.handlers.scroll);
    }
    state.scrollTarget = target;
    state.handlers.scroll = updateHeaderOnScroll;
    target.addEventListener("scroll", state.handlers.scroll, { passive: true });
    updateHeaderOnScroll();
  }

  const theme = cfg.theme === "light" ? "light" : "dark";
  const palette = theme === "light"
    ? {
        bg: "linear-gradient(180deg,#2f8f70 0%,#3aa37b 48%,#2f7d65 100%)",
        border: "rgba(16,115,82,.22)",
        text: "#173f32",
        muted: "#557568",
        tile: "rgba(255,255,255,.82)",
        tileBorder: "rgba(16,115,82,.16)",
        active: "linear-gradient(145deg,#e9f8f1 0%,#d7f1e5 52%,#c8eadc 100%)",
        activeText: "#315f50",
        shadow: "0 14px 34px rgba(45,80,67,.16)",
        logo: "linear-gradient(145deg,#e9f8f1 0%,#d7f1e5 55%,#c8eadc 100%)",
        logoText: "#315f50"
      }
    : {
        bg: "linear-gradient(180deg,#13072c 0%,#1b0a3d 48%,#110625 100%)",
        border: "rgba(167,139,250,.30)",
        text: "#f4efff",
        muted: "#a997d4",
        tile: "rgba(255,255,255,.045)",
        tileBorder: "rgba(167,139,250,.22)",
        active: "linear-gradient(145deg,#8b5cf6 0%,#6d28d9 55%,#4c1d95 100%)",
        activeText: "#ffffff",
        shadow: "0 16px 38px rgba(0,0,0,.34)",
        logo: "linear-gradient(145deg,#8b5cf6,#5b21b6)"
      };

  removeNode(RAIL_ID);
  removeNode(FLYOUT_ID);
  removeNode(STYLE_ID);
  doc.body.classList.remove(BODY_CLASS, HEADER_HIDDEN_CLASS);
  doc.querySelectorAll(`.${NATIVE_HIDDEN_CLASS}`).forEach((node) => {
    node.classList.remove(NATIVE_HIDDEN_CLASS);
    node.removeAttribute("aria-hidden");
  });

  const style = doc.createElement("style");
  style.id = STYLE_ID;
  style.textContent = `
    .${NATIVE_HIDDEN_CLASS} {
      display:none !important;
      visibility:hidden !important;
      opacity:0 !important;
      pointer-events:none !important;
    }


    #${RAIL_ID} {
      position:fixed;
      inset:0 auto 0 0;
      width:82px;
      height:100vh;
      z-index:1000000;
      display:none;
      flex-direction:column;
      align-items:center;
      box-sizing:border-box;
      padding:14px 10px 13px;
      background:${palette.bg};
      border-right:1px solid ${palette.border};
      box-shadow:${palette.shadow};
      overflow-y:auto;
      overflow-x:hidden;
      scrollbar-width:none;
      backdrop-filter:blur(18px);
    }
    #${RAIL_ID}::-webkit-scrollbar { display:none; }
    body.${BODY_CLASS} #${RAIL_ID} { display:flex; }

    body.${BODY_CLASS} [data-testid="stAppViewContainer"] {
      margin-left:82px !important;
      width:calc(100% - 82px) !important;
      max-width:calc(100% - 82px) !important;
      box-sizing:border-box !important;
      transition:none !important;
    }
    body.${BODY_CLASS} [data-testid="stHeader"] {
      /* stAppViewContainer already carries the 82px rail offset.  Keeping the
         header at left:0 avoids applying that offset twice, which previously
         created the empty purple gap and a second-looking arrow area. */
      left:0 !important;
      width:100% !important;
      max-width:100% !important;
      box-sizing:border-box !important;
      border-left:0 !important;
      transition:transform .18s ease, opacity .18s ease !important;
    }

    /* The header is visible at the top, then slides away once the user scrolls.
       This prevents KPI cards and page content from being covered by a frozen bar. */
    body.${HEADER_HIDDEN_CLASS} [data-testid="stHeader"] {
      transform:translateY(-105%) !important;
      opacity:0 !important;
      pointer-events:none !important;
    }

    .pf-rail-open,
    .pf-rail-logo,
    .pf-rail-item {
      appearance:none;
      border:0;
      outline:0;
      cursor:pointer;
      display:flex;
      align-items:center;
      justify-content:center;
      flex:0 0 auto;
    }
    .pf-rail-open {
      width:54px;
      height:42px;
      margin:0 0 12px;
      border-radius:14px;
      color:${palette.text};
      background:${palette.tile};
      border:1px solid ${palette.tileBorder};
      box-shadow:0 8px 20px rgba(0,0,0,.06);
      transition:background .16s ease,color .16s ease,transform .16s ease,border-color .16s ease;
    }
    .pf-rail-open:hover {
      color:${palette.activeText};
      background:${palette.active};
      border-color:rgba(255,255,255,.28);
      transform:translateX(2px);
    }
    .pf-rail-logo {
      width:52px;
      height:52px;
      border-radius:18px;
      margin:8px 0 16px;
      color:#fff;
      background:${palette.logo};
      color:${palette.logoText};
      border:1px solid rgba(47,143,112,.25);
      box-shadow:0 10px 24px rgba(47,143,112,.20);
    }
    .pf-rail-separator {
      width:44px;
      height:1px;
      background:${palette.border};
      margin:0 0 11px;
    }
    .pf-rail-items {
      width:100%;
      display:flex;
      flex-direction:column;
      align-items:center;
      gap:8px;
    }
    .pf-rail-item {
      position:relative;
      width:54px;
      height:54px;
      border-radius:17px;
      color:${palette.muted};
      background:${palette.tile};
      border:1px solid ${palette.tileBorder};
      box-shadow:0 8px 20px rgba(0,0,0,.055);
      transition:transform .16s ease,background .16s ease,color .16s ease,border-color .16s ease,box-shadow .16s ease;
    }
    .pf-rail-item:hover {
      transform:translateY(-2px);
      color:${palette.text};
      border-color:${palette.border};
      box-shadow:0 12px 24px rgba(0,0,0,.12);
    }
    .pf-rail-item.is-active {
      color:${palette.activeText};
      background:${palette.active};
      border-color:rgba(47,143,112,.25);
      box-shadow:0 10px 24px rgba(47,143,112,.20);
    }
    .pf-rail-item svg,
    .pf-rail-logo svg,
    .pf-rail-open svg {
      width:23px;
      height:23px;
      stroke:currentColor;
      fill:none;
      stroke-width:1.85;
      stroke-linecap:round;
      stroke-linejoin:round;
      pointer-events:none;
    }
    .pf-rail-open svg { width:21px; height:21px; }
    .pf-rail-logo svg { width:25px; height:25px; }
    .pf-rail-tooltip {
      position:absolute;
      left:64px;
      top:50%;
      transform:translate(5px,-50%);
      opacity:0;
      visibility:hidden;
      white-space:nowrap;
      padding:7px 10px;
      border-radius:10px;
      background:${theme === "light" ? "#143c31" : "#f6f1ff"};
      color:${theme === "light" ? "#fff" : "#1b0a3d"};
      font:800 11px/1.1 Inter,system-ui,sans-serif;
      box-shadow:0 10px 28px rgba(0,0,0,.22);
      transition:opacity .14s ease,transform .14s ease,visibility .14s ease;
      pointer-events:none;
      z-index:1000002;
    }
    .pf-rail-item:hover .pf-rail-tooltip {
      opacity:1;
      visibility:visible;
      transform:translate(0,-50%);
    }
    .pf-rail-item[aria-expanded="true"] {
      color:${palette.activeText};
      background:${palette.active};
      border-color:${palette.border};
      box-shadow:0 12px 26px rgba(0,0,0,.16);
    }
    .pf-rail-item.has-children::after {
      content:"";
      position:absolute;
      right:5px;
      top:50%;
      width:4px;
      height:4px;
      border-radius:50%;
      background:currentColor;
      opacity:.72;
      transform:translateY(-50%);
    }
    #${FLYOUT_ID} {
      position:fixed;
      left:92px;
      top:90px;
      z-index:1000003;
      min-width:238px;
      max-width:300px;
      max-height:calc(100vh - 28px);
      overflow:auto;
      padding:12px;
      border-radius:18px;
      background:${theme === "light" ? "rgba(250,255,252,.97)" : "rgba(25,10,57,.98)"};
      border:1px solid ${palette.border};
      box-shadow:0 18px 50px rgba(0,0,0,${theme === "light" ? ".18" : ".42"});
      backdrop-filter:blur(20px);
      opacity:0;
      visibility:hidden;
      transform:translateX(-8px) scale(.985);
      transform-origin:left center;
      pointer-events:none;
      transition:opacity .16s ease,transform .16s ease,visibility .16s ease;
      scrollbar-width:thin;
      color:${palette.text};
    }
    #${FLYOUT_ID}.is-open {
      opacity:1;
      visibility:visible;
      transform:translateX(0) scale(1);
      pointer-events:auto;
    }
    .pf-rail-flyout-title {
      padding:5px 8px 10px;
      font:900 12px/1.25 Inter,system-ui,sans-serif;
      letter-spacing:.08em;
      text-transform:uppercase;
      color:${palette.text};
      border-bottom:1px solid ${palette.border};
      margin-bottom:7px;
    }
    .pf-rail-child {
      width:100%;
      min-height:44px;
      display:flex;
      align-items:center;
      gap:10px;
      padding:9px 10px;
      margin:4px 0;
      border-radius:12px;
      border:1px solid transparent;
      background:transparent;
      color:${palette.text};
      cursor:pointer;
      text-align:left;
      font:800 12px/1.25 Inter,system-ui,sans-serif;
      transition:background .14s ease,border-color .14s ease,transform .14s ease,color .14s ease;
    }
    .pf-rail-child:hover {
      background:${theme === "light" ? "rgba(47,143,112,.10)" : "rgba(139,92,246,.16)"};
      border-color:${palette.border};
      transform:translateX(2px);
    }
    .pf-rail-child.is-active {
      background:${palette.active};
      color:${palette.activeText};
      border-color:${palette.border};
    }
    .pf-rail-child-icon {
      width:28px;
      height:28px;
      flex:0 0 28px;
      border-radius:9px;
      display:grid;
      place-items:center;
      background:${theme === "light" ? "rgba(47,143,112,.12)" : "rgba(139,92,246,.18)"};
      color:inherit;
      font:900 15px/1 Inter,system-ui,sans-serif;
    }
    .pf-rail-child-label { flex:1; }

    @media (max-width:700px) {
      #${RAIL_ID} { width:70px; padding-left:7px; padding-right:7px; }
      body.${BODY_CLASS} [data-testid="stAppViewContainer"] {
        margin-left:70px !important;
        width:calc(100% - 70px) !important;
        max-width:calc(100% - 70px) !important;
      }
      body.${BODY_CLASS} [data-testid="stHeader"] {
        left:0 !important;
        width:100% !important;
        max-width:100% !important;
      }
      .pf-rail-item { width:48px; height:48px; border-radius:15px; }
      .pf-rail-logo { width:48px; height:48px; }
      .pf-rail-open { width:48px; }
    }
  `;
  doc.head.appendChild(style);

  const rail = doc.createElement("nav");
  rail.id = RAIL_ID;
  rail.setAttribute("aria-label", "Navigasi ringkas");


  const logo = doc.createElement("button");
  logo.type = "button";
  logo.className = "pf-rail-logo";
  logo.title = "Auto EDA Insight";
  logo.setAttribute("aria-label", "Auto EDA Insight");
  logo.innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 3 21 12 12 21 3 12 12 3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/></svg>';
  logo.addEventListener("click", () => navigateTo("Dashboard"));
  rail.appendChild(logo);

  const separator = doc.createElement("div");
  separator.className = "pf-rail-separator";
  rail.appendChild(separator);

  const flyout = doc.createElement("div");
  flyout.id = FLYOUT_ID;
  flyout.setAttribute("role", "menu");
  flyout.setAttribute("aria-hidden", "true");
  doc.body.appendChild(flyout);

  function closeFlyout() {
    if (state.activeFlyout && state.activeFlyout.button) {
      state.activeFlyout.button.setAttribute("aria-expanded", "false");
    }
    state.activeFlyout = null;
    flyout.classList.remove("is-open");
    flyout.setAttribute("aria-hidden", "true");
  }

  function positionFlyout(button) {
    const rect = button.getBoundingClientRect();
    const railRect = rail.getBoundingClientRect();
    const desiredTop = rect.top - 6;
    const maxTop = Math.max(12, hostWindow.innerHeight - flyout.offsetHeight - 12);
    flyout.style.left = `${Math.round(railRect.right + 10)}px`;
    flyout.style.top = `${Math.round(Math.max(12, Math.min(desiredTop, maxTop)))}px`;
  }

  function openFlyout(item, button) {
    const children = Array.isArray(item.children) ? item.children : [];
    if (!children.length) {
      closeFlyout();
      navigateTo(item.target || item.label, item.group || item.label);
      return;
    }
    if (state.activeFlyout && state.activeFlyout.label === item.label) {
      closeFlyout();
      return;
    }

    if (state.activeFlyout && state.activeFlyout.button) {
      state.activeFlyout.button.setAttribute("aria-expanded", "false");
    }
    flyout.replaceChildren();

    const title = doc.createElement("div");
    title.className = "pf-rail-flyout-title";
    title.textContent = item.label || "Menu";
    flyout.appendChild(title);

    children.forEach((child) => {
      const childButton = doc.createElement("button");
      childButton.type = "button";
      childButton.className = "pf-rail-child" + (child.active ? " is-active" : "");
      childButton.setAttribute("role", "menuitem");
      childButton.setAttribute("aria-label", child.label || child.target || "Menu");

      const icon = doc.createElement("span");
      icon.className = "pf-rail-child-icon";
      icon.textContent = child.icon || "•";
      const label = doc.createElement("span");
      label.className = "pf-rail-child-label";
      label.textContent = child.label || child.target || "Menu";
      childButton.append(icon, label);

      childButton.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        closeFlyout();
        navigateTo(child.target || child.label, item.group || item.label);
      });
      flyout.appendChild(childButton);
    });

    state.activeFlyout = { label: item.label, button };
    button.setAttribute("aria-expanded", "true");
    flyout.classList.add("is-open");
    flyout.setAttribute("aria-hidden", "false");
    hostWindow.requestAnimationFrame(() => positionFlyout(button));
  }

  const itemsWrap = doc.createElement("div");
  itemsWrap.className = "pf-rail-items";
  (cfg.items || []).forEach((item) => {
    const button = doc.createElement("button");
    button.type = "button";
    const hasChildren = Array.isArray(item.children) && item.children.length > 0;
    button.className = "pf-rail-item" + (item.active ? " is-active" : "") + (hasChildren ? " has-children" : "");
    button.title = item.label || "";
    button.setAttribute("aria-label", item.label || "");
    button.setAttribute("aria-haspopup", hasChildren ? "menu" : "false");
    button.setAttribute("aria-expanded", "false");
    button.innerHTML = `${item.icon || ""}<span class="pf-rail-tooltip">${item.label || ""}</span>`;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openFlyout(item, button);
    });
    itemsWrap.appendChild(button);
  });
  rail.appendChild(itemsWrap);
  doc.body.appendChild(rail);

  function syncLayout() {
    if (state.destroyed) return;
    const sidebar = sidebarElement();
    if (!sidebar) return;

    bindSidebar(sidebar);
    bindHeader();
    bindScrollTarget();

    const collapsed = isSidebarCollapsed(sidebar);
    state.lastCollapsed = collapsed;
    if (!collapsed) closeFlyout();
    doc.body.classList.toggle(BODY_CLASS, collapsed);
    /* Keep exactly one opener: Streamlit's native control in the left side of
       the header. The compact rail itself no longer renders an open button. */
    setNativeOpenControlsHidden(false);
  }

  state.handlers.resize = function () {
    closeFlyout();
    scheduleSync();
  };
  state.handlers.keydown = function (event) {
    if (event.key === "Escape") closeFlyout();
  };
  state.handlers.documentClick = function (event) {
    const rawTarget = event.target;
    if (rawTarget && rawTarget.closest && !rawTarget.closest(`#${RAIL_ID}`) && !rawTarget.closest(`#${FLYOUT_ID}`)) {
      closeFlyout();
    }
    const target = rawTarget && rawTarget.closest ? rawTarget.closest("button") : null;
    if (!target) return;
    if (
      target.closest('section[data-testid="stSidebar"]') ||
      isNativeSidebarControl(target) ||
      target.closest(`#${RAIL_ID}`)
    ) {
      later(scheduleSync, 30);
      later(scheduleSync, 180);
      later(scheduleSync, 360);
    }
  };

  hostWindow.addEventListener("resize", state.handlers.resize, { passive: true });
  doc.addEventListener("click", state.handlers.documentClick, true);
  doc.addEventListener("keydown", state.handlers.keydown, true);

  state.destroy = function destroy() {
    if (state.destroyed) return;
    state.destroyed = true;

    if (state.rafId !== null) hostWindow.cancelAnimationFrame(state.rafId);
    state.timers.forEach((id) => hostWindow.clearTimeout(id));
    state.timers = [];

    if (state.sidebarObserver) state.sidebarObserver.disconnect();
    if (state.sidebarResizeObserver) state.sidebarResizeObserver.disconnect();
    if (state.headerObserver) state.headerObserver.disconnect();
    if (state.scrollTarget && state.handlers.scroll) {
      state.scrollTarget.removeEventListener("scroll", state.handlers.scroll);
    }
    hostWindow.removeEventListener("resize", state.handlers.resize);
    doc.removeEventListener("click", state.handlers.documentClick, true);
    doc.removeEventListener("keydown", state.handlers.keydown, true);

    removeNode(RAIL_ID);
    removeNode(FLYOUT_ID);
    removeNode(STYLE_ID);
    doc.body.classList.remove(BODY_CLASS, HEADER_HIDDEN_CLASS);
    doc.querySelectorAll(`.${NATIVE_HIDDEN_CLASS}`).forEach((node) => {
      node.classList.remove(NATIVE_HIDDEN_CLASS);
      node.removeAttribute("aria-hidden");
    });

    if (hostWindow[STATE_KEY] === state) delete hostWindow[STATE_KEY];
  };

  syncLayout();
  later(scheduleSync, 80);
  later(scheduleSync, 260);
  later(scheduleSync, 650);
  later(scheduleSync, 1200);
})();
