const Settings = {
  prefs: {
    installed: false,
    version: '',
    os: '',
    video_quality: 'highres',
    video_size: 'expand',
    video_speed: '1',
    volume: 'default',
    volumelevel: '100',
    subtitles: 'off',
    annotationsoff: false,
    autoexpanddescription: false,
    suggestedautoplay: true,
    youtubevideoautoplaybehavior: 'default',
    embeddedvideoautoplaybehavior: 'default',
    playlistvideoautoplaybehavior: 'default',
  },
  async get(item) {
    return (await chrome.storage.sync.get({ [item]: Settings.prefs[item] }))[
      item
    ];
  },
  async getAll() {
    return await chrome.storage.sync.get(null);
  },
  async set(item) {
    await chrome.storage.sync.set(item);
  },
  async clear() {
    await chrome.storage.sync.clear();
  },
};
export default Settings;
