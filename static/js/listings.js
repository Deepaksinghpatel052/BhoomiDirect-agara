/* Buy Property: AJAX filtering, pagination and grid/list toggle */
(function ($) {
  "use strict";
  $(function () {
    const $form = $("#filterForm"), $results = $("#results");
    if (!$form.length) return;
    let view = "grid";
    try { view = localStorage.getItem("bd_view") || "grid"; } catch (e) { /* ignore */ }

    function applyView() {
      $results.toggleClass("list-view", view === "list");
      $("[data-view]").removeClass("active").filter('[data-view="' + view + '"]').addClass("active");
    }
    applyView();

    function load(page) {
      let params = $form.serialize();
      if (page) params += "&page=" + page;
      $results.css("opacity", 0.45);
      $.get($form.attr("action") || window.location.pathname, params)
        .done(function (res) {
          $results.html(res.html).css("opacity", 1);
          $("#resultCount").text(res.total);
          applyView();
          history.replaceState(null, "", "?" + params);
        })
        .fail(function () {
          $results.css("opacity", 1);
          showToast("Could not load properties. Please try again.", "danger");
        });
    }

    $form.on("change", "select", function () { load(); });
    $form.on("submit", function (e) { e.preventDefault(); load(); });
    $results.on("click", ".pagination a[data-page]", function (e) {
      e.preventDefault();
      load($(this).data("page"));
      $("html, body").animate({ scrollTop: $results.offset().top - 110 }, 250);
    });
    $("[data-view]").on("click", function () {
      view = $(this).data("view");
      try { localStorage.setItem("bd_view", view); } catch (e) { /* ignore */ }
      applyView();
    });
  });
})(jQuery);
