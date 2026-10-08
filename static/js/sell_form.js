/* Sell Your Property multi-step form: conditional fields, map pin, unit converter, uploads. */
(function ($) {
  "use strict";

  function readJSON(id) {
    const el = document.getElementById(id);
    return el ? JSON.parse(el.textContent) : null;
  }

  $(function () {
    const $form = $("#sellForm");
    if (!$form.length) return;
    $form.hide().fadeIn(300);

    const factors = readJSON("unit-factors") || {};
    const agriTypes = readJSON("agri-types") || [];

    // ------------------------------------------------------------------
    // Step 2: property type cards
    // ------------------------------------------------------------------
    $form.on("change", ".type-radio input", function () {
      $(".type-radio label").removeClass("checked");
      $(this).closest("label").addClass("checked");
    });

    // Tehsil -> locality filtering, and centre the map on the chosen locality
    const localityData = readJSON("locality-data");
    const $tehsil = $("#id_tehsil"), $locality = $("#id_locality");
    let pickerMap = null, pickerMarker = null;

    if (localityData && $locality.length) {
      const $allOptions = $locality.find("option").clone();
      function filterLocalities() {
        const tehsil = $tehsil.val();
        const current = $locality.val();
        $locality.empty();
        $allOptions.each(function () {
          const v = $(this).val();
          if (!v || !tehsil || String(localityData[v].tehsil) === String(tehsil)) $locality.append($(this).clone());
        });
        if ($locality.find('option[value="' + current + '"]').length) $locality.val(current);
        else $locality.val("");
      }
      $tehsil.on("change", filterLocalities);
      filterLocalities();

      $locality.on("change", function () {
        const info = localityData[$(this).val()];
        if (info && !$tehsil.val()) $tehsil.val(info.tehsil);
        if (info && pickerMap) pickerMap.setView([info.lat, info.lng], 14);
      });
    }

    // Leaflet pin picker
    if ($("#mapPicker").length && typeof L !== "undefined") {
      const $lat = $("#id_latitude"), $lng = $("#id_longitude");
      let start = [27.1767, 78.0081], zoom = 11;
      if ($lat.val() && $lng.val()) { start = [parseFloat($lat.val()), parseFloat($lng.val())]; zoom = 15; }
      else if (localityData && localityData[$locality.val()]) {
        const l = localityData[$locality.val()]; start = [l.lat, l.lng]; zoom = 14;
      }
      pickerMap = L.map("mapPicker").setView(start, zoom);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19, attribution: "&copy; OpenStreetMap",
        referrerPolicy: "strict-origin-when-cross-origin", // OSM requires a Referer (see main.js)
      }).addTo(pickerMap);

      function placePin(latlng) {
        const lat = latlng.lat.toFixed(6), lng = latlng.lng.toFixed(6);
        if (pickerMarker) pickerMarker.setLatLng(latlng);
        else {
          pickerMarker = L.marker(latlng, { draggable: true }).addTo(pickerMap);
          pickerMarker.on("dragend", function (e) { placePin(e.target.getLatLng()); });
        }
        $lat.val(lat); $lng.val(lng);
        $("#pinLabel").html('<i class="bi bi-pin-map-fill text-terracotta"></i> Pin placed at ' + lat + ", " + lng);
      }
      if ($lat.val() && $lng.val()) placePin(L.latLng(start[0], start[1]));
      pickerMap.on("click", function (e) { placePin(e.latlng); });

      $("#useMyLocation").on("click", function () {
        if (!navigator.geolocation) return showToast("Location is not available on this device.", "warning");
        navigator.geolocation.getCurrentPosition(
          function (pos) {
            const ll = L.latLng(pos.coords.latitude, pos.coords.longitude);
            pickerMap.setView(ll, 16); placePin(ll);
          },
          function () { showToast("Could not get your location. Please tap on the map.", "warning"); }
        );
      });
    }

    // ------------------------------------------------------------------
    // Step 3: live unit converter
    // ------------------------------------------------------------------
    const $areaValue = $("[data-area-value]"), $areaUnit = $("[data-area-unit]");
    function fmt(n) {
      if (!isFinite(n)) return "—";
      if (n >= 100) return Math.round(n).toLocaleString("en-IN");
      return n.toLocaleString("en-IN", { maximumFractionDigits: 3 });
    }
    function updateConverter() {
      const value = parseFloat($areaValue.val());
      const unit = $areaUnit.val();
      $("#unitConverter .val").each(function () {
        const target = $(this).data("unit");
        if (!value || !factors[unit]) { $(this).text("—"); return; }
        $(this).text(fmt((value * factors[unit]) / factors[target]));
      });
    }
    $areaValue.on("input", updateConverter);
    $areaUnit.on("change", updateConverter);
    updateConverter();

    // ------------------------------------------------------------------
    // Step 4: conditional legal fields
    // ------------------------------------------------------------------
    function toggleJoint() {
      const joint = $("#id_ownership_type").val() === "joint";
      $(".js-joint-only").toggle(joint);
      if (!joint) $("#id_number_of_owners").val(1);
    }
    function toggleEncumbrance() {
      const show = $("#id_has_loan").is(":checked") || $("#id_has_dispute").is(":checked");
      $(".js-encumbrance").toggle(show);
    }
    if ($("#id_ownership_type").length) {
      $("#id_ownership_type").on("change", toggleJoint); toggleJoint();
      $("#id_has_loan, #id_has_dispute").on("change", toggleEncumbrance); toggleEncumbrance();
    }

    // ------------------------------------------------------------------
    // Step 5: price in words + photo dropzone
    // ------------------------------------------------------------------
    const $price = $("[data-price-input]");
    function priceWords() {
      const v = parseFloat($price.val());
      $("#priceWords").text(v ? "= " + formatINRShort(v) + "  (" + formatINR(v) + ")" : "");
    }
    $price.on("input", priceWords); priceWords();

    const input = document.querySelector('[data-dropzone-input="photos"]');
    const $drop = $("#photoDrop");
    if (input && $drop.length) {
      const MAX_MB = 5, MAX_FILES = 10;
      let store = new DataTransfer();

      function render() {
        const $grid = $("#photoPreview").empty();
        Array.from(store.files).forEach(function (file, idx) {
          const $item = $('<div class="item"><img alt=""><span></span>' +
            '<button type="button" class="btn btn-sm btn-light position-absolute top-0 end-0 m-1 p-0 px-1" aria-label="Remove">&times;</button></div>');
          $item.find("span").text(file.name);
          const reader = new FileReader();
          reader.onload = function (e) { $item.find("img").attr("src", e.target.result).attr("alt", "Preview of " + file.name); };
          reader.readAsDataURL(file);
          $item.find("button").on("click", function () {
            const next = new DataTransfer();
            Array.from(store.files).forEach(function (f, i) { if (i !== idx) next.items.add(f); });
            store = next; input.files = store.files; render();
          });
          $grid.append($item);
        });
      }

      function addFiles(files) {
        Array.from(files).forEach(function (file) {
          if (!/^image\/(jpeg|png|webp)$/.test(file.type)) return showToast(file.name + ": only JPG, PNG or WebP images.", "danger");
          if (file.size > MAX_MB * 1024 * 1024) return showToast(file.name + " is larger than " + MAX_MB + " MB.", "danger");
          if (store.files.length >= MAX_FILES) return showToast("Maximum " + MAX_FILES + " photos.", "warning");
          store.items.add(file);
        });
        input.files = store.files;
        render();
      }

      $drop.on("click keypress", function () { input.click(); });
      $(input).on("change", function () {
        const picked = Array.from(this.files);
        this.files = store.files; // keep earlier files
        addFiles(picked);
      });
      $drop.on("dragover dragenter", function (e) { e.preventDefault(); $drop.addClass("dragover"); });
      $drop.on("dragleave drop", function (e) { e.preventDefault(); $drop.removeClass("dragover"); });
      $drop.on("drop", function (e) { addFiles(e.originalEvent.dataTransfer.files); });
    }

    $("[data-doc-input]").on("change", function () {
      Array.from(this.files).forEach((f) => {
        if (f.size > 10 * 1024 * 1024) { showToast(f.name + " is larger than 10 MB.", "danger"); this.value = ""; }
      });
    });

    // ------------------------------------------------------------------
    // Client-side required-field validation before submit
    // ------------------------------------------------------------------
    $form.on("submit", function (e) {
      let firstBad = null;
      $form.find(".js-req-error").remove();
      $form.find("[required]").each(function () {
        const $f = $(this);
        if (!$f.is(":visible") && $f.attr("type") !== "radio") return;
        let empty;
        if ($f.attr("type") === "checkbox") empty = !$f.is(":checked");
        else if ($f.attr("type") === "radio") empty = !$form.find('input[name="' + $f.attr("name") + '"]:checked').length;
        else empty = !$.trim($f.val());
        if (empty) {
          $f.addClass("is-invalid");
          const $wrap = $f.closest("[data-field]");
          if (!$wrap.find(".invalid-feedback.d-block").length) $wrap.append('<div class="invalid-feedback d-block js-req-error">This field is required.</div>');
          firstBad = firstBad || $f;
        } else {
          $f.removeClass("is-invalid");
        }
      });
      if (firstBad) {
        e.preventDefault();
        showToast("Please fill the required fields.", "danger");
        $("html, body").animate({ scrollTop: firstBad.closest("[data-field]").offset().top - 120 }, 300);
        return;
      }
      $("#nextBtn").prop("disabled", true).html('<span class="spinner-border spinner-border-sm"></span> Saving...');
    });
    $form.on("input change", ".is-invalid", function () { $(this).removeClass("is-invalid"); });
  });
})(jQuery);
