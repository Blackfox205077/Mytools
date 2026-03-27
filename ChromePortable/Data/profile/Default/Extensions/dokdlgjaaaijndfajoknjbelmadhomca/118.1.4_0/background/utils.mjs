const Utils = {
  openOptionsPage() {
    const onOpened = () => {};
    const onError = _error => {};
    chrome.runtime.openOptionsPage().then(onOpened, onError);
  },
  requestPermissions() {},
  async getActiveTab(type = 'last') {
    const queryOptions = {
      active: true,
      ...(type === 'last'
        ? { lastFocusedWindow: true }
        : { currentWindow: true }),
    };
    const [tab] = await chrome.tabs.query(queryOptions);
    return tab;
  },
  async oRTCT(p) {
    const tab = await Utils.getActiveTab();
    const options = { url: p['url'], ...(tab && { index: tab.index + 1 }) };
    chrome.tabs.create(options);
  },
};
export default Utils;
