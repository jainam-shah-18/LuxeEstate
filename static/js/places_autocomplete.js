(function () {
  const input = document.getElementById('place-search');
  const addr = document.getElementById('id_address');
  if (!input || !window.google || !google.maps || !google.maps.places) return;

  const ac = new google.maps.places.Autocomplete(input, { fields: ['name', 'place_id', 'geometry', 'formatted_address'] });
  ac.addListener('place_changed', function () {
    const place = ac.getPlace();
    if (!place.geometry) return;
    const rows = document.querySelectorAll('[id^="id_nearby-"][id$="-name"]');
    let target = null;
    for (const el of rows) {
      if (!el.value.trim()) {
        target = el;
        break;
      }
    }
    if (!target) {
      alert('Add a new empty nearby row (save & edit) or clear a name field.');
      return;
    }
    const m = target.id.match(/nearby-(\d+)/);
    const idx = m ? m[1] : '0';
    target.value = place.name || '';
    const pid = document.getElementById('id_nearby-' + idx + '-place_id');
    const lat = document.getElementById('id_nearby-' + idx + '-latitude');
    const lng = document.getElementById('id_nearby-' + idx + '-longitude');
    if (pid) pid.value = place.place_id || '';
    if (lat) lat.value = place.geometry.location.lat();
    if (lng) lng.value = place.geometry.location.lng();
    if (addr && !addr.value.trim()) addr.value = place.formatted_address || '';
  });
})();
