/* Staff dashboard: charts, Kanban drag & drop, live evaluation score, legal progress */
(function ($) {
  "use strict";
  const GREEN = "#1f5f3f", TERRA = "#b5502f", GOLD = "#c8963e";
  const PALETTE = [GREEN, TERRA, GOLD, "#3c8b5f", "#d97a55", "#8fb08f", "#6b5b95", "#5f6b63"];

  $(function () {
    $("#sidebarToggle").on("click", function () { $("#dashSidebar").toggleClass("open"); });
    $(document).on("click", function (e) {
      if (!$(e.target).closest("#dashSidebar, #sidebarToggle").length) $("#dashSidebar").removeClass("open");
    });

    // ---------------- Charts ----------------
    const chartEl = document.getElementById("chart-data");
    if (chartEl && typeof Chart !== "undefined") {
      const d = JSON.parse(chartEl.textContent);
      Chart.defaults.font.family = "Inter, sans-serif";
      Chart.defaults.color = "#5f6b63";
      new Chart(document.getElementById("chartWeeks"), {
        type: "line",
        data: { labels: d.weeks.labels, datasets: [{ label: "Leads", data: d.weeks.data, borderColor: GREEN, backgroundColor: "rgba(31,95,63,.12)", fill: true, tension: 0.35, pointRadius: 4 }] },
        options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
      });
      new Chart(document.getElementById("chartLocality"), {
        type: "bar",
        data: { labels: d.locality.labels, datasets: [{ label: "Leads", data: d.locality.data, backgroundColor: TERRA, borderRadius: 6 }] },
        options: { indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, ticks: { precision: 0 } } } },
      });
      new Chart(document.getElementById("chartType"), {
        type: "doughnut",
        data: { labels: d.type.labels, datasets: [{ data: d.type.data, backgroundColor: PALETTE, borderWidth: 2 }] },
        options: { maintainAspectRatio: false, plugins: { legend: { position: "right", labels: { boxWidth: 12 } } }, cutout: "62%" },
      });
      new Chart(document.getElementById("chartFunnel"), {
        type: "bar",
        data: { labels: d.funnel.labels, datasets: [{ label: "Leads reached stage", data: d.funnel.data, backgroundColor: d.funnel.data.map((_, i) => i === d.funnel.data.length - 1 ? GREEN : GOLD), borderRadius: 6 }] },
        options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
      });
    }

    // ---------------- Kanban ----------------
    const $lists = $(".kanban-list");
    if ($lists.length && $.fn.sortable) {
      $lists.sortable({
        connectWith: ".kanban-list",
        placeholder: "kanban-placeholder",
        tolerance: "pointer",
        revert: 120,
        receive: function (event, ui) {
          const $card = ui.item, $from = ui.sender, status = $(this).data("status");
          $.post($("#kanban").data("move-url"), { pk: $card.data("pk"), status: status })
            .done(function (res) { showToast(res.message, "success"); updateCounts(); })
            .fail(function (xhr) {
              $from.sortable("cancel");
              updateCounts();
              showToast((xhr.responseJSON && xhr.responseJSON.message) || "Could not move lead.", "danger");
            });
        },
      }).disableSelection();
    }
    function updateCounts() {
      $(".kanban-col").each(function () { $(this).find(".col-count").text($(this).find(".kanban-card").length); });
    }

    // ---------------- Live evaluation score ----------------
    const $scores = $(".score-input");
    function recalc() {
      let total = 0;
      $scores.each(function () {
        const v = parseInt(this.value, 10) || 0;
        total += v;
        $(this).closest(".score-row").find(".score-val").text(v);
      });
      const pct = Math.round((total / 60) * 100);
      let rec = "Reject", css = "danger";
      if (total >= 45) { rec = "Strong Buy"; css = "success"; } else if (total >= 30) { rec = "Consider"; css = "warning"; }
      $("#scoreTotal").text(total);
      $("#scoreBar").css("width", pct + "%").removeClass("bg-success bg-warning bg-danger").addClass("bg-" + css);
      $("#scoreRec").text(rec).removeClass("text-bg-success text-bg-warning text-bg-danger").addClass("text-bg-" + css);
      const resale = parseFloat($("#id_estimated_resale_value").val());
      const buy = parseFloat($("#scoreTotal").data("buy-price"));
      if (resale && buy) {
        const margin = ((resale - buy) * 100) / buy;
        $("#marginLive").text(margin.toFixed(1) + "%").toggleClass("text-danger", margin < 0).toggleClass("text-green", margin >= 0);
      }
    }
    if ($scores.length) { $scores.on("input change", recalc); $("#id_estimated_resale_value").on("input", recalc); recalc(); }

    // ---------------- Legal checklist progress ----------------
    const $legal = $("[data-legal-item]");
    function legalProgress() {
      const done = $legal.filter(":checked").length, pct = Math.round((done / $legal.length) * 100);
      $("#legalBar").css("width", pct + "%").text(pct + "%");
    }
    if ($legal.length) { $legal.on("change", legalProgress); legalProgress(); }

    // ---------------- Price helper text ----------------
    $("[data-price-input]").each(function () {
      const $in = $(this), $hint = $('<div class="form-text fw-semibold text-green"></div>').insertAfter($in);
      function upd() { const v = parseFloat($in.val()); $hint.text(v ? formatINRShort(v) : ""); }
      $in.on("input", upd); upd();
    });

    // ---------------- Inquiry status AJAX ----------------
    $(document).on("change", ".js-inquiry-status", function () {
      const $s = $(this);
      $.post($s.data("url"), { status: $s.val() })
        .done(function (res) { showToast(res.message || "Updated", "success"); })
        .fail(function () { showToast("Update failed", "danger"); });
    });

    // Sold price prompt
    $(document).on("submit", ".js-listing-status", function (e) {
      const $f = $(this);
      if ($f.find("[name=status]").val() === "sold" && !$f.data("asked")) {
        const price = prompt("Final sale price in ₹ (leave blank to use listing price):", $f.data("price"));
        if (price === null) { e.preventDefault(); return; }
        $f.find("[name=sold_price]").val(price);
      }
    });

    // Remember last open tab on lead detail
    const tabKey = "bd_lead_tab";
    $('a[data-bs-toggle="tab"]').on("shown.bs.tab", function (e) { try { localStorage.setItem(tabKey, $(e.target).attr("href")); } catch (err) { /* ignore */ } });
    try {
      const last = localStorage.getItem(tabKey) || "";
      if (/^#[\w-]+$/.test(last) && $('a[href="' + last + '"]').length) bootstrap.Tab.getOrCreateInstance($('a[href="' + last + '"]')[0]).show();
    } catch (err) { /* ignore */ }
  });
})(jQuery);
