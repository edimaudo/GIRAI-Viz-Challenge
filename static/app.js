(() => {
  const meta = window.GIRAI_META;
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => [...document.querySelectorAll(sel)];
  const state = {
    view: 'overall',
    metric: 'Overall index',
    pillar: 'Thematic score',
    region: 'All regions',
    currentCountry: null,
    rankSort: 'ranking',
    rankDirection: 'asc',
    comparisonMode: 'regions',
    comparisonFirst: meta.regions[0],
    comparisonSecond: meta.regions[1],
  };

  const chartIds = ['mapChart', 'regionalChart', 'pillarChart', 'ladderChart', 'countryChart', 'comparisonChart'];

  function chartScale() {
    const map = { small: 0.92, medium: 1, large: 1.16 };
    return map[document.body.dataset.scale] || 1;
  }

  function chartTheme() {
    const dark = document.documentElement.dataset.theme === 'dark';
    return {
      font: dark ? '#F1F4F5' : '#171717',
      muted: dark ? '#B8C2C8' : '#5F686E',
      grid: dark ? '#354249' : '#C7D1D7',
      paper: 'rgba(0,0,0,0)',
      land: dark ? '#303B40' : '#D8DEE2',
      ocean: dark ? '#181D20' : '#F2F5F6',
    };
  }

  function patchLayout(layout) {
    const t = chartTheme();
    const out = JSON.parse(JSON.stringify(layout || {}));
    out.paper_bgcolor = t.paper;
    out.plot_bgcolor = t.paper;
    const scale = chartScale();
    out.font = { ...(out.font || {}), color: t.font, size: Math.round((out.font?.size || 12) * scale) };
    if (out.title) out.title = { ...out.title, font: { ...(out.title.font || {}), color: t.font, size: Math.round((out.title.font?.size || 15) * scale) } };
    if (out.xaxis) out.xaxis = { ...out.xaxis, gridcolor: t.grid, tickcolor: t.grid, titlefont: { ...(out.xaxis.titlefont || {}), color: t.muted, size: Math.round((out.xaxis.titlefont?.size || 12) * scale) }, tickfont: { ...(out.xaxis.tickfont || {}), color: t.font, size: Math.round((out.xaxis.tickfont?.size || 10) * scale) } };
    if (out.yaxis) out.yaxis = { ...out.yaxis, gridcolor: t.grid, tickcolor: t.grid, titlefont: { ...(out.yaxis.titlefont || {}), color: t.muted, size: Math.round((out.yaxis.titlefont?.size || 12) * scale) }, tickfont: { ...(out.yaxis.tickfont || {}), color: t.font, size: Math.round((out.yaxis.tickfont?.size || 10) * scale) } };
    if (out.geo) out.geo = { ...out.geo, landcolor: t.land, oceancolor: t.ocean };
    if (out.legend) out.legend = { ...out.legend, font: { ...(out.legend.font || {}), color: t.font, size: Math.round((out.legend.font?.size || 10) * scale) } };
    return out;
  }

  async function getJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    return res.json();
  }

  function fillSelect(select, options, value) {
    if (!select) return;
    select.innerHTML = '';
    options.forEach(o => {
      const opt = document.createElement('option');
      if (typeof o === 'object') {
        opt.value = o.value;
        opt.textContent = o.label;
      } else {
        opt.value = o;
        opt.textContent = o;
      }
      select.appendChild(opt);
    });
    if (options.some(o => (typeof o === 'object' ? o.value : o) === value)) select.value = value;
  }

  function metricOptions() {
    if (state.view === 'overall') return ['Overall index'];
    if (state.view === 'dimension') return meta.dimensions;
    return meta.themes;
  }

  function countryRowsForRegion() {
    return state.region === 'All regions'
      ? meta.country_options
      : meta.country_options.filter(c => c.region === state.region);
  }

  function syncCountrySelects() {
    const rows = countryRowsForRegion();
    const valid = new Set(rows.map(c => c.iso3));
    if (state.currentCountry && !valid.has(state.currentCountry)) {
      state.currentCountry = null;
      hideProfile();
    }

    const options = [
      { value: '', label: 'All countries' },
      ...rows.map(c => ({ value: c.iso3, label: state.region === 'All regions' ? `${c.country} — ${c.region}` : c.country })),
    ];
    fillSelect($('#countrySelectData'), options, state.currentCountry || '');
    fillSelect($('#countrySelectRank'), options, state.currentCountry || '');
    const hasCountry = Boolean(state.currentCountry);
    $('#clearCountryButton').hidden = !hasCountry;
    $('#countrySelectData').setAttribute('aria-label', state.region === 'All regions' ? 'Country filter across all regions' : `Country filter within ${state.region}`);
    $('#countrySelectRank').setAttribute('aria-label', state.region === 'All regions' ? 'Country filter across all regions' : `Country filter within ${state.region}`);
  }

  function syncControls() {
    fillSelect($('#metricSelect'), metricOptions(), state.metric);
    $('#pillarUnit').hidden = state.view !== 'thematic';
    if (state.view === 'thematic') {
      fillSelect($('#pillarSelect'), meta.theme_pillar_options, meta.theme_pillar_options.includes(state.pillar) ? state.pillar : 'Thematic score');
      state.pillar = $('#pillarSelect').value;
    }
    $('#metricUnit').querySelector('label').textContent = state.view === 'thematic' ? 'Thematic area' : 'Measure';
    fillSelect($('#regionSelect'), ['All regions', ...meta.regions], state.region);
    fillSelect($('#rankRegion'), ['All regions', ...meta.regions], state.region);
    syncCountrySelects();
  }

  function urlParams(includeCountry = false) {
    const params = new URLSearchParams({ view: state.view, metric: state.metric, pillar: state.pillar, region: state.region });
    if (includeCountry && state.currentCountry) params.set('country', state.currentCountry);
    return params;
  }

  function updateURL() {
    const params = urlParams(true).toString();
    history.replaceState({}, '', params ? `${location.pathname}?${params}` : location.pathname);
  }

  function renderPlot(id, figure) {
    const el = document.getElementById(id);
    if (!el || !window.Plotly) return;
    Plotly.react(el, figure.data || [], patchLayout(figure.layout || {}), {
      responsive: true,
      displayModeBar: false,
      scrollZoom: false,
    });
  }

  function updateMapLegend() {
    const colors = ['#EEF4F7', '#D7E7EF', '#B3CFDE', '#7FA9BF', '#4C829F', '#154E70'];
    $$('.legend-swatch').forEach((swatch, i) => { swatch.style.background = colors[i]; });
  }

  async function loadExplore() {
    const qs = urlParams(false);
    try {
      const [data, map, regional, pillars, ladder] = await Promise.all([
        getJSON(`/api/explore?${qs}`),
        getJSON(`/api/figure/map?${qs}`),
        getJSON(`/api/figure/regional?${qs}`),
        getJSON(`/api/figure/pillars?${qs}`),
        getJSON(`/api/figure/theme_ladder?${qs}`),
      ]);
      $('#headlineTitle').textContent = data.headline.title;
      $('#headlineSub').textContent = data.headline.sub;
      $('#headlineRegional').textContent = data.headline.regional;
      $('#medianValue').textContent = data.headline.median == null ? '—' : Number(data.headline.median).toFixed(1);
      $('#countryCount').textContent = data.headline.countries;

      const mapLabel = state.view === 'thematic'
        ? `${state.metric} — ${state.pillar}`
        : (state.view === 'dimension' ? state.metric : 'Overall index score');
      $('#mapTitle').textContent = mapLabel;
      $('#mapContext').textContent = state.region;
      $('#pillarTitle').textContent = state.view === 'thematic' ? `${state.metric} — pillar profile` : 'Pillar profile';
      $('#pillarSubtitle').textContent = state.view === 'thematic'
        ? `Median scores inside ${state.metric}.`
        : (state.region === 'All regions' ? 'Median scores across all countries.' : `Median scores for ${state.region}.`);

      const dim = state.view === 'dimension' ? state.metric : (meta.theme_dimension[state.metric] || 'Human Rights and AI');
      $('#ladderTitle').textContent = `${dim} thematic ladder`;
      $('#ladderSubtitle').textContent = state.region === 'All regions'
        ? 'Median thematic scores inside the selected dimension.'
        : `Median thematic scores for ${state.region}.`;

      renderPlot('mapChart', map);
      renderPlot('regionalChart', regional);
      renderPlot('pillarChart', pillars);
      renderPlot('ladderChart', ladder);
      updateMapLegend();
      syncCountrySelects();
      updateURL();
    } catch (err) {
      $('#headlineTitle').textContent = 'The visualization could not load.';
      $('#headlineSub').textContent = err.message;
    }
  }

  let mapWired = false;
  function wireMapClicks() {
    const map = $('#mapChart');
    if (!map || mapWired) return;
    mapWired = true;
    map.on('plotly_click', async (evt) => {
      const point = evt.points?.[0];
      if (!point?.customdata?.[0]) return;
      await selectCountry(point.customdata[0]);
    });
  }

  function setCountrySelectValue(iso3) {
    ['#countrySelectData', '#countrySelectRank'].forEach(sel => {
      const el = $(sel);
      if (el) el.value = iso3 || '';
    });
  }

  async function selectCountry(iso3) {
    try {
      const country = meta.country_options.find(c => c.iso3 === iso3);
      if (!country) return;
      if (state.region !== 'All regions' && country.region !== state.region) {
        state.region = country.region;
        syncControls();
        await loadExplore();
      }
      const profile = await getJSON(`/api/country/${encodeURIComponent(iso3)}`);
      state.currentCountry = iso3;
      setCountrySelectValue(iso3);
      syncCountrySelects();
      await showProfile(profile);
      await loadRankings();
      updateURL();
    } catch (err) {
      console.error(err);
    }
  }

  function hideProfile() {
    const panel = $('#profilePanel');
    if (panel) panel.hidden = true;
    const layout = $('#rankingContentGrid');
    if (layout) layout.classList.remove('has-profile');
    $('#profileHeading').textContent = 'Select a row.';
    $('#profileMeta').textContent = 'The selected country’s dimensions, pillars and thematic areas.';
    $('#profileIndex').textContent = '—';
    $('#profileThemes').innerHTML = '';
    const chart = $('#countryChart');
    if (chart && chart.data) Plotly.purge(chart);
  }

  async function showProfile(profile) {
    const r = profile.summary;
    $('#profileHeading').textContent = r.country;
    $('#profileMeta').textContent = `${r.region} · rank ${r.ranking} · ${r.iso3}`;
    $('#profileIndex').textContent = Number(r.index_score).toFixed(2);
    $('#profileThemes').innerHTML = '';
    profile.themes.forEach(t => {
      const row = document.createElement('div');
      row.className = 'theme-item';
      row.innerHTML = `<span>${escapeHTML(t.thematic_area)}</span><span>${Number(t.ta_score).toFixed(1)}</span>`;
      $('#profileThemes').appendChild(row);
    });
    const fig = await getJSON(`/api/figure/country_profile?iso3=${encodeURIComponent(r.iso3)}`);
    renderPlot('countryChart', fig);
    $('#profilePanel').hidden = false;
    $('#rankingContentGrid').classList.add('has-profile');
  }

  function escapeHTML(s) {
    return String(s).replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
  }

  async function loadRankings() {
    const p = new URLSearchParams({
      region: state.region,
      sort: state.rankSort,
      direction: state.rankDirection,
    });
    if (state.currentCountry) p.set('iso3', state.currentCountry);

    try {
      const rows = await getJSON(`/api/rankings?${p}`);
      const body = $('#rankingBody');
      body.innerHTML = '';
      $('#rankingCount').textContent = rows.length;
      $('#rankingCountLabel').textContent = rows.length === 1 ? 'country & jurisdiction shown' : 'countries & jurisdictions shown';

      rows.forEach(r => {
        const tr = document.createElement('tr');
        tr.dataset.iso3 = r.iso3;
        tr.tabIndex = 0;
        tr.setAttribute('aria-selected', state.currentCountry === r.iso3 ? 'true' : 'false');
        tr.innerHTML = `
          <td>${r.ranking}</td>
          <td class="country-col"><strong>${escapeHTML(r.country)}</strong><div class="muted-code">${r.iso3}</div></td>
          <td>${escapeHTML(r.region)}</td>
          <td class="num"><strong>${Number(r.index_score).toFixed(2)}</strong></td>
          <td class="num">${Number(r.human_rights_score).toFixed(1)}</td>
          <td class="num">${Number(r.governance_score).toFixed(1)}</td>
          <td class="num">${Number(r.capacities_score).toFixed(1)}</td>`;
        tr.addEventListener('click', () => selectCountry(r.iso3));
        tr.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectCountry(r.iso3); }
        });
        body.appendChild(tr);
      });
      syncCountrySelects();
      if (!state.currentCountry) hideProfile();
    } catch (err) {
      $('#rankingCount').textContent = '—';
      $('#rankingCountLabel').textContent = 'countries & jurisdictions shown';
      $('#rankingBody').innerHTML = `<tr><td colspan="7">${escapeHTML(err.message)}</td></tr>`;
    }
  }

  function getCountryOptionsForRegion() {
    return countryRowsForRegion().map(c => ({
      value: c.iso3,
      label: state.region === 'All regions' ? `${c.country} — ${c.region}` : c.country,
    }));
  }

  function syncComparisonRegions() {
    fillSelect($('#compareFirst'), meta.regions, state.comparisonFirst);
    fillSelect($('#compareSecond'), meta.regions, state.comparisonSecond);
    if ($('#compareFirst').value === $('#compareSecond').value) {
      const alternate = meta.regions.find(r => r !== $('#compareFirst').value);
      $('#compareSecond').value = alternate || meta.regions[1];
      state.comparisonSecond = $('#compareSecond').value;
    }
  }

  function syncComparisonCountryOptions() {
    const options = getCountryOptionsForRegion();
    if (options.length < 2) {
      fillSelect($('#compareFirst'), options, options[0]?.value || '');
      fillSelect($('#compareSecond'), options, options[0]?.value || '');
      return;
    }
    const valid = new Set(options.map(o => o.value));
    if (!valid.has(state.comparisonFirst)) state.comparisonFirst = options[0].value;
    if (!valid.has(state.comparisonSecond) || state.comparisonSecond === state.comparisonFirst) {
      state.comparisonSecond = (options.find(o => o.value !== state.comparisonFirst) || options[0]).value;
    }
    fillSelect($('#compareFirst'), options, state.comparisonFirst);
    fillSelect($('#compareSecond'), options, state.comparisonSecond);
  }

  function syncComparisonControls() {
    const regionsMode = state.comparisonMode === 'regions';
    $$('.comparison-mode-button').forEach(btn => {
      const active = btn.dataset.mode === state.comparisonMode;
      btn.classList.toggle('is-active', active);
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
    $('#comparisonRegionUnit').querySelector('label').textContent = regionsMode ? 'Region 1' : 'Country 1';
    $('#comparisonRegionUnitSecond').querySelector('label').textContent = regionsMode ? 'Region 2' : 'Country 2';
    if (regionsMode) syncComparisonRegions(); else syncComparisonCountryOptions();
  }

  async function loadComparison() {
    syncComparisonControls();
    const first = $('#compareFirst').value;
    const second = $('#compareSecond').value;
    if (!first || !second || first === second) {
      $('#comparisonNote').textContent = 'Choose two different selections.';
      return;
    }
    $('#comparisonNote').textContent = 'Comparison uses median scores for regions and published scores for countries.';
    try {
      const params = new URLSearchParams({ mode: state.comparisonMode, first, second });
      const fig = await getJSON(`/api/figure/comparison?${params}`);
      renderPlot('comparisonChart', fig);
    } catch (err) {
      $('#comparisonNote').textContent = err.message;
    }
  }

  function activateTab(id) {
    $$('.tab-button').forEach(btn => {
      const active = btn.dataset.tab === id;
      btn.classList.toggle('is-active', active);
      btn.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    $$('.tab-panel').forEach(panel => panel.hidden = panel.id !== id);
    if (id === 'rankingsTab') {
      loadRankings();
      loadComparison();
    }
  }

  function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('girai-theme', theme);
    const dark = theme === 'dark';
    $('#themeToggle').textContent = dark ? 'Light mode' : 'Dark mode';
    $('#themeToggle').setAttribute('aria-pressed', dark ? 'true' : 'false');
    chartIds.forEach(id => {
      const el = document.getElementById(id);
      if (el && el.data) Plotly.relayout(el, patchLayout(el.layout));
    });
    updateMapLegend();
  }

  function setScale(scale) {
    document.body.dataset.scale = scale;
    localStorage.setItem('girai-scale', scale);
    $$('button[data-scale]').forEach(btn => btn.setAttribute('aria-pressed', btn.dataset.scale === scale ? 'true' : 'false'));
    chartIds.forEach(id => {
      const el = document.getElementById(id);
      if (el && el.data) Plotly.relayout(el, patchLayout(el.layout));
    });
  }

  function initFromURL() {
    const p = new URLSearchParams(location.search);
    if (['overall', 'dimension', 'thematic'].includes(p.get('view'))) state.view = p.get('view');
    if (p.get('metric')) state.metric = p.get('metric');
    if (p.get('pillar')) state.pillar = p.get('pillar');
    if (p.get('region')) state.region = p.get('region');
    if (p.get('country')) state.currentCountry = p.get('country').toUpperCase();
    if (!meta.country_options.some(c => c.iso3 === state.currentCountry)) state.currentCountry = null;
    syncControls();
  }

  function wireEvents() {
    $$('.tab-button').forEach(btn => btn.addEventListener('click', () => activateTab(btn.dataset.tab)));
    $('#viewSelect').addEventListener('change', () => {
      state.view = $('#viewSelect').value;
      state.metric = metricOptions()[0];
      syncControls();
      loadExplore();
    });
    $('#metricSelect').addEventListener('change', () => { state.metric = $('#metricSelect').value; loadExplore(); });
    $('#pillarSelect').addEventListener('change', () => { state.pillar = $('#pillarSelect').value; loadExplore(); });

    const handleRegionChange = () => {
      state.region = $('#regionSelect').value;
      syncControls();
      loadExplore();
      loadRankings();
      if (!$('#rankingsTab').hidden) loadComparison();
    };
    $('#regionSelect').addEventListener('change', handleRegionChange);
    $('#rankRegion').addEventListener('change', () => {
      state.region = $('#rankRegion').value;
      syncControls();
      loadExplore();
      loadRankings();
      loadComparison();
    });

    const handleCountryChange = (source) => {
      const value = $(source).value;
      if (!value) {
        clearCountry();
      } else {
        selectCountry(value);
      }
    };
    $('#countrySelectData').addEventListener('change', () => handleCountryChange('#countrySelectData'));
    $('#countrySelectRank').addEventListener('change', () => handleCountryChange('#countrySelectRank'));
    $('#clearCountryButton').addEventListener('click', clearCountry);
    $('#profileClearButton').addEventListener('click', clearCountry);

    $('#rankSort').addEventListener('change', () => { state.rankSort = $('#rankSort').value; loadRankings(); });
    $('#rankDirection').addEventListener('change', () => { state.rankDirection = $('#rankDirection').value; loadRankings(); });
    $('#themeToggle').addEventListener('click', () => setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));
    $$('button[data-scale]').forEach(btn => btn.addEventListener('click', () => setScale(btn.dataset.scale)));
    $$('.comparison-mode-button').forEach(btn => btn.addEventListener('click', () => {
      state.comparisonMode = btn.dataset.mode;
      syncComparisonControls();
      loadComparison();
    }));
    $('#compareFirst').addEventListener('change', () => {
      state.comparisonFirst = $('#compareFirst').value;
      loadComparison();
    });
    $('#compareSecond').addEventListener('change', () => {
      state.comparisonSecond = $('#compareSecond').value;
      loadComparison();
    });
  }

  async function clearCountry() {
    state.currentCountry = null;
    syncCountrySelects();
    hideProfile();
    await loadRankings();
    updateURL();
  }

  async function start() {
    const savedTheme = localStorage.getItem('girai-theme') || 'light';
    const savedScale = localStorage.getItem('girai-scale') || 'medium';
    setTheme(savedTheme);
    setScale(savedScale);
    initFromURL();
    $('#viewSelect').value = state.view;
    $('#rankRegion').value = state.region;
    wireEvents();
    await loadExplore();
    wireMapClicks();
    syncComparisonControls();
    if (state.currentCountry) {
      await selectCountry(state.currentCountry);
    }
  }

  start().catch(console.error);
})();
