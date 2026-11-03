/*
 * LeadsFlo conversion-intent tracking.
 * A calendar CTA click is NOT a confirmed appointment.
 * Do not log generate_lead or purchase events here.
 */
(function () {
  "use strict";

  function sendEvent(name, parameters) {
    if (typeof window.gtag === "function") {
      window.gtag("event", name, parameters);
    }
  }

  function getBookingAnchor(target) {
    if (!(target instanceof Element)) return null;

    var anchor = target.closest("a[href]");
    if (!anchor) return null;

    try {
      var url = new URL(anchor.href, window.location.href);

      if (url.hostname !== "calendar.app.google") {
        return null;
      }

      return anchor;
    } catch (_) {
      return null;
    }
  }

  document.addEventListener("click", function (event) {
    var anchor = getBookingAnchor(event.target);
    if (!anchor) return;

    var label = (anchor.textContent || "")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 100);

    sendEvent("book_call_click", {
      booking_provider: "google_calendar",
      page_path: window.location.pathname,
      cta_text: label,
      link_url: anchor.href
    });
  }, true);
})();
