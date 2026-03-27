import Utils from '../background/utils.mjs';
import Settings from '../background/settings.mjs';
const $ = selector => document.querySelector(selector);
const Popup = {
  async init() {
    const os = (await chrome.runtime.getPlatformInfo()).os;
    if (os === 'android') $('#popup')?.classList.add('android');
    const prefs = await Settings.getAll();
    Popup.adjustOptions(prefs);
  },
  selectOption(selectElement, requiredValue) {
    for (let i = 0; i < selectElement.options.length; i++) {
      let option = selectElement.options[i];
      if (option.value === requiredValue) {
        option.selected = true;
        break;
      }
    }
  },
  adjustOptions({
    video_quality,
    video_size,
    video_speed,
    annotationsoff,
    volume,
    volumelevel,
    subtitles,
    youtubevideoautoplaybehavior,
    playlistvideoautoplaybehavior,
    suggestedautoplay,
    embeddedvideoautoplaybehavior,
    autoexpanddescription,
  }) {
    const v_q = $('#video_quality');
    if (v_q && v_q instanceof HTMLSelectElement) {
      Popup.selectOption(v_q, video_quality);
      v_q.addEventListener('change', Popup.reqVQSChange);
    }
    const v_s = $('#video_size');
    if (v_s && v_s instanceof HTMLSelectElement) {
      Popup.selectOption(v_s, video_size);
      v_s.addEventListener('change', Popup.reqVQSChange);
    }
    const v_sp = $('#video_speed');
    if (v_sp && v_sp instanceof HTMLSelectElement) {
      Popup.selectOption(v_sp, video_speed);
      v_sp.addEventListener('change', Popup.reqVQSChange);
    }
    const a_of = $('#annotationsoff');
    if (a_of && a_of instanceof HTMLInputElement) {
      a_of.checked = annotationsoff;
      a_of.addEventListener('change', Popup.reqVQSChange);
    }
    const vol = $('#volume');
    const vol_radio = $('#volume input[type="radio"].vol_' + volume + '');
    if (vol && vol_radio && vol_radio instanceof HTMLInputElement) {
      vol_radio.checked = true;
      vol.addEventListener('change', Popup.reqVQSChange);
    }
    const vol_level = $('#volumelevel');
    const vol_level_in = $('#volumelevelinput');
    if (
      vol_level &&
      vol_level instanceof HTMLInputElement &&
      vol_level_in &&
      vol_level_in instanceof HTMLInputElement
    ) {
      vol_level.value = volumelevel;
      vol_level.addEventListener('focus', () => {
        vol_level_in.checked = true;
      });
      vol_level.addEventListener('change', Popup.reqVQSChange);
    }
    const sbt = $('#subtitles');
    const sbt_radio = $(
      '#subtitles input[type="radio"].subtitles_' + subtitles + '',
    );
    if (sbt && sbt_radio && sbt_radio instanceof HTMLInputElement) {
      sbt_radio.checked = true;
      sbt.addEventListener('change', Popup.reqVQSChange);
    }
    const yt_apb = $('#youtubevideoautoplaybehavior');
    const yt_apb_opt = $(
      '#youtubevideoautoplaybehavior [value="' +
        youtubevideoautoplaybehavior +
        '"]',
    );
    if (yt_apb && yt_apb_opt && yt_apb_opt instanceof HTMLOptionElement) {
      yt_apb_opt.selected = true;
      yt_apb.addEventListener('change', Popup.reqVQSChange);
    }
    const pl_apb = $('#playlistvideoautoplaybehavior');
    const pl_apb_opt = $(
      '#playlistvideoautoplaybehavior [value="' +
        playlistvideoautoplaybehavior +
        '"]',
    );
    if (pl_apb && pl_apb_opt && pl_apb_opt instanceof HTMLOptionElement) {
      pl_apb_opt.selected = true;
      pl_apb.addEventListener('change', Popup.reqVQSChange);
    }
    const sg_ap = $('#suggestedautoplay');
    if (sg_ap && sg_ap instanceof HTMLInputElement) {
      sg_ap.checked = suggestedautoplay;
      sg_ap.addEventListener('change', Popup.reqVQSChange);
    }
    const emb_apb = $('#embeddedvideoautoplaybehavior');
    const emb_apb_opt = $(
      '#embeddedvideoautoplaybehavior [value="' +
        embeddedvideoautoplaybehavior +
        '"]',
    );
    if (emb_apb && emb_apb_opt && emb_apb_opt instanceof HTMLOptionElement) {
      emb_apb_opt.selected = true;
      emb_apb.addEventListener('change', Popup.reqVQSChange);
    }
    const auto_ed = $('#autoexpanddescription');
    if (auto_ed && auto_ed instanceof HTMLInputElement) {
      auto_ed.checked = autoexpanddescription;
      auto_ed.addEventListener('change', Popup.reqVQSChange);
    }
  },
  reqVQSChange() {
    const new_prefs = {};
    const valObj = {
      video_quality: { s: '#video_quality', p: 'value' },
      video_size: { s: '#video_size', p: 'value' },
      video_speed: { s: '#video_speed', p: 'value' },
      annotationsoff: { s: '#annotationsoff', p: 'checked' },
      volume: {
        s: '#volume input[type="radio"][name="volume"]:checked',
        p: 'value',
      },
      volumelevel: { s: '#volumelevel', p: 'value' },
      subtitles: {
        s: '#subtitles input[type="radio"][name="subtitles"]:checked',
        p: 'value',
      },
      youtubevideoautoplaybehavior: {
        s: '#youtubevideoautoplaybehavior',
        p: 'value',
      },
      playlistvideoautoplaybehavior: {
        s: '#playlistvideoautoplaybehavior',
        p: 'value',
      },
      suggestedautoplay: { s: '#suggestedautoplay', p: 'checked' },
      embeddedvideoautoplaybehavior: {
        s: '#embeddedvideoautoplaybehavior',
        p: 'value',
      },
      autoexpanddescription: { s: '#autoexpanddescription', p: 'checked' },
    };
    for (const [key, value] of Object.entries(valObj)) {
      const elem = $(value.s);
      if (elem && value.p in elem) {
        new_prefs[key] = elem[value.p];
      } else {
      }
    }
    (async () => {
      const tab = await Utils.getActiveTab('current');
      try {
        if (tab && typeof tab.id === 'number') {
          await chrome.tabs.sendMessage(tab.id, {
            action: 'video_qualitysize_change',
            ...new_prefs,
            isOptionHandle: true,
          });
        }
      } catch (e) {}
    })();
    Settings.set({ ...new_prefs });
  },
};
Popup.init();
