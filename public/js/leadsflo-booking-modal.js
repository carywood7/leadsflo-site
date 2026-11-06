/* LEADSFLO_UNIFIED_BOOKING_V1 */
(function () {
  "use strict";

  if (document.getElementById("lp-book-dialog")) return;

  const bookingURL = "https:" + "//calendar.app.google/1fpawLr6fgP7Hmoi7";
  const embedURL = "https:" + "//calendar.google.com/calendar/appointments/schedules/" + "AcZssZ0VnOAytUM-31S2nb6WehVDQqrQti-mjJTQJ5oOFlN1ctyMnZNBpPLxihgQ5cjsP3kZDz3F5BXo?gv=true";

  const css = document.createElement("style");
  css.textContent = `
    .lf-book-dialog {
      width:min(940px,calc(100vw - 24px));
      height:min(850px,94dvh);
      max-width:none;max-height:none;
      margin:auto;padding:0;border:0;
      border-radius:16px;background:#fff;
      color:#173149;overflow:hidden;
      box-shadow:0 25px 90px #06142680;
    }
    .lf-book-dialog::backdrop {
      background:#07162abf;
      backdrop-filter:blur(5px);
    }
    .lf-book-shell {
      display:flex;flex-direction:column;height:100%;
    }
    .lf-book-head {
      display:flex;align-items:center;
      justify-content:space-between;gap:15px;
      padding:18px 24px;background:#f8f3ea;
      border-bottom:1px solid #e6dfd4;
    }
    .lf-book-head span {
      font:800 10px/1.5 system-ui,sans-serif;
      letter-spacing:.13em;color:#926d40;
    }
    .lf-book-head h2 {
      margin:4px 0 0;color:#183a40;
      font:700 clamp(19px,3vw,26px)/1.25 system-ui,sans-serif;
    }
    .lf-book-close {
      width:40px;height:40px;flex:0 0 40px;
      border:1px solid #d5dce1;border-radius:50%;
      background:white;color:#173149;
      font-size:26px;cursor:pointer;
    }
    .lf-book-frame {
      flex:1;min-height:0;
    }
    .lf-book-frame iframe {
      display:block;width:100%;height:100%;border:0;
    }
    .lf-book-foot {
      display:flex;justify-content:space-between;
      flex-wrap:wrap;gap:10px;padding:13px 22px;
      background:#f8f3ea;font:12px system-ui,sans-serif;
    }
    .lf-book-foot a {color:#285dbe}
    @media(max-width:600px) {
      .lf-book-dialog {height:96dvh;width:calc(100vw - 12px)}
      .lf-book-head {padding:12px 14px}
      .lf-book-foot {padding:10px 14px}
    }
  `;
  document.head.appendChild(css);

  let dialog;
  let lastTrigger;

  function getDialog() {
    if (dialog) return dialog;
    dialog = document.createElement("dialog");
    dialog.className = "lf-book-dialog";
    dialog.setAttribute("aria-labelledby", "lf-book-title");

    dialog.innerHTML = `
      <div class="lf-book-shell">
        <header class="lf-book-head">
          <div>
            <span>LEADSFLO / GROWTH STRATEGY CALL</span>
            <h2 id="lf-book-title">Book your 15-minute call</h2>
          </div>
          <button class="lf-book-close" type="button"
            aria-label="Close booking calendar">×</button>
        </header>
        <div class="lf-book-frame">
          <iframe title="LeadsFlo Growth Strategy Call booking"
            loading="lazy"
            referrerpolicy="strict-origin-when-cross-origin"></iframe>
        </div>
        <footer class="lf-book-foot">
          <span>Choose an available time above.</span>
          <a href="${bookingURL}" target="_blank"
            rel="noopener noreferrer">Calendar not loading? Open booking page</a>
        </footer>
      </div>`;

    dialog.querySelector(".lf-book-close").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", e => {
      if (e.target === dialog) dialog.close();
    });
    dialog.addEventListener("close", () => lastTrigger?.focus());
    document.body.appendChild(dialog);
    return dialog;
  }

  document.addEventListener("click", event => {
    const anchor = event.target instanceof Element
      ? event.target.closest("a[href]") : null;
    if (!anchor) return;

    let url;
    try { url = new URL(anchor.href); }
    catch (_) { return; }
    if (url.hostname !== "calendar.app.google") return;

    const modal = getDialog();
    if (typeof modal.showModal !== "function") return;

    event.preventDefault();
    lastTrigger = anchor;

    const frame = modal.querySelector("iframe");
    if (!frame.getAttribute("src")) frame.src = embedURL;
    if (!modal.open) modal.showModal();
  });
})();

/* LEADSFLO_BOOKING_ATTENTION_LOADER_V1 */
(function () {
  if (document.getElementById("lf-booking-attention-css")) return;

  const css = document.createElement("link");
  css.id = "lf-booking-attention-css";
  css.rel = "stylesheet";
  css.href = "/css/leadsflo-booking-attention.css";
  document.head.appendChild(css);

  document.querySelectorAll("a[href]").forEach(anchor => {
    let url;
    try {
      url = new URL(anchor.href);
    } catch (_) {
      return;
    }

    if (url.hostname !== "calendar.app.google") return;

    const classes = anchor.className;
    if (typeof classes !== "string") return;

    if (/button|btn|cta|book|action|sticky|navcta/i.test(classes)) {
      anchor.classList.add("lf-booking-attention");
    }
  });
})();
