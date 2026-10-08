/* BhoomiDirect Agra - global site behaviour (jQuery) */
(function ($) {
  "use strict";

  // ---- CSRF for AJAX -----------------------------------------------------
  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]*)"));
    return match ? decodeURIComponent(match[2]) : null;
  }
  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
      }
      xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
    },
  });

  // ---- Toasts (used by AJAX actions everywhere) ---------------------------
  window.showToast = function (message, type) {
    const tone = { success: "text-bg-success", danger: "text-bg-danger", warning: "text-bg-warning", info: "text-bg-dark" }[type || "success"];
    const $toast = $(
      '<div class="toast align-items-center border-0 ' + tone + '" role="status" aria-live="polite" aria-atomic="true">' +
        '<div class="d-flex"><div class="toast-body"></div>' +
        '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div></div>'
    );
    $toast.find(".toast-body").text(message);
    $("#toastArea").append($toast);
    const t = new bootstrap.Toast($toast[0], { delay: 3500 });
    t.show();
    $toast.on("hidden.bs.toast", function () { $toast.remove(); });
  };

  // ---- Indian money formatting (mirrors the Django filter) ---------------
  window.formatINR = function (num) {
    num = Math.round(Number(num) || 0);
    const s = String(Math.abs(num));
    let last3 = s.slice(-3), rest = s.slice(0, -3);
    if (rest) last3 = "," + last3;
    rest = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",");
    return "₹ " + (num < 0 ? "-" : "") + rest + last3;
  };
  window.formatINRShort = function (num) {
    num = Number(num) || 0;
    const trim = (v) => String(Number(v.toFixed(2)));
    if (num >= 1e7) return "₹ " + trim(num / 1e7) + " Crore";
    if (num >= 1e5) return "₹ " + trim(num / 1e5) + " Lakh";
    return window.formatINR(num);
  };

  $(function () {
    // ---- Language toggle placeholder (EN / हिंदी) ---------------------------
    function setLang(lang) {
      $("body").toggleClass("lang-hi", lang === "hi");
      $(".lang-toggle button").removeClass("active").filter('[data-lang="' + lang + '"]').addClass("active");
      try { localStorage.setItem("bd_lang", lang); } catch (e) { /* storage unavailable */ }
    }
    let saved = "en";
    try { saved = localStorage.getItem("bd_lang") || "en"; } catch (e) { /* ignore */ }
    const urlLang = new URLSearchParams(window.location.search).get("lang");
    if (urlLang === "hi" || urlLang === "en") saved = urlLang; // shareable ?lang=hi links
    setLang(saved);
    $(".lang-toggle button").on("click", function () {
      const lang = $(this).data("lang");
      setLang(lang);
      if (lang === "hi") showToast("हिंदी: मुख्य बटन और हीरो सेक्शन का अनुवाद (डेमो). Full Hindi site in next phase.", "info");
    });

    // ---- Animated counters --------------------------------------------------
    const $counters = $("[data-count]");
    function runCounter(el) {
      const $el = $(el);
      if ($el.data("done")) return;
      $el.data("done", true);
      const target = parseFloat($el.data("count"));
      const decimals = ($el.data("count").toString().split(".")[1] || "").length;
      $({ n: 0 }).animate({ n: target }, {
        duration: 1800,
        easing: "swing",
        step: function (now) { $el.text(now.toLocaleString("en-IN", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })); },
        complete: function () { $el.text(target.toLocaleString("en-IN", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })); },
      });
    }
    if ($counters.length) {
      if ("IntersectionObserver" in window) {
        const io = new IntersectionObserver(function (entries) {
          entries.forEach(function (e) { if (e.isIntersecting) { runCounter(e.target); io.unobserve(e.target); } });
        }, { threshold: 0.4 });
        $counters.each(function () { io.observe(this); });
      } else {
        $counters.each(function () { runCounter(this); });
      }
    }

    // ---- Indian mobile number inputs: digits only, max 10 ------------------
    const phoneRe = /^[6-9]\d{9}$/;
    $(document).on("input", "input[data-phone]", function () {
      this.value = this.value.replace(/\D/g, "").slice(0, 10);
      $(this).removeClass("is-invalid");
    });
    $(document).on("blur", "input[data-phone]", function () {
      if (this.value && !phoneRe.test(this.value)) {
        $(this).addClass("is-invalid");
        if (!$(this).next(".js-phone-error").length) {
          $(this).after('<div class="invalid-feedback js-phone-error">Enter a valid 10 digit mobile number starting with 6-9.</div>');
        }
      }
    });
    $(document).on("submit", "form", function (e) {
      let ok = true;
      $(this).find("input[data-phone]").each(function () {
        const required = $(this).prop("required");
        if ((this.value || required) && !phoneRe.test(this.value)) {
          $(this).addClass("is-invalid").trigger("blur");
          ok = false;
        }
      });
      if (!ok) {
        e.preventDefault();
        e.stopImmediatePropagation();
        showToast("Please enter a valid 10 digit mobile number.", "danger");
      }
    });

    // Mark server-side errors on inputs
    $(".invalid-feedback.d-block").each(function () {
      $(this).closest("[data-field]").find("input, select, textarea").not("[type=checkbox],[type=radio]").addClass("is-invalid");
    });

    // ---- Generic Leaflet map: <div data-map='{"lat":..,"lng":..}' data-points-id="json-script-id"> --------
    $("[data-map]").each(function () {
      if (typeof L === "undefined") return;
      const cfg = $(this).data("map");
      const map = L.map(this, { scrollWheelZoom: false }).setView([cfg.lat, cfg.lng], cfg.zoom || 11);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(map);
      const pointsId = $(this).data("points-id");
      const icon = L.divIcon({
        className: "",
        html: '<div style="background:#b5502f;width:16px;height:16px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.35)"></div>',
        iconSize: [16, 16],
      });
      if (pointsId) {
        const points = JSON.parse(document.getElementById(pointsId).textContent);
        const group = [];
        points.forEach(function (p) {
          const m = L.marker([p.lat, p.lng], { icon: icon }).addTo(map);
          const link = p.url ? '<br><a href="' + p.url + '">Sell land here &rarr;</a>' : "";
          m.bindPopup("<strong>" + $("<div>").text(p.name).html() + "</strong>" + (p.type ? "<br><small>" + p.type + "</small>" : "") + link);
          group.push([p.lat, p.lng]);
        });
        if (group.length > 1 && !cfg.fixed) map.fitBounds(group, { padding: [30, 30] });
      } else {
        L.marker([cfg.lat, cfg.lng], { icon: icon }).addTo(map).bindPopup(cfg.label || "");
      }
    });

    // ---- Demo-only buttons ---------------------------------------------------
    $(document).on("click", "[data-demo]", function (e) {
      e.preventDefault();
      showToast($(this).data("demo") || "Demo: this feature is part of the full version.", "info");
    });

    // ---- WhatsApp share --------------------------------------------------
    $(document).on("click", "[data-copy]", function () {
      const text = $(this).data("copy");
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(function () { showToast("Copied: " + text); });
    });
  });
})(jQuery);
