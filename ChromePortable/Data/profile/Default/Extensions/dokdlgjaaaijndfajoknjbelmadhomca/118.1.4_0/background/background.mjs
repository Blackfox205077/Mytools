import Utils from './utils.mjs';
import Extension from './extension.mjs';
import Settings from './settings.mjs';
const Background = {
  async init() {
    chrome.runtime.onInstalled.addListener(Background.onInstalledListener);
    await Background.updateSettings();
    Background.setAction();
    chrome.runtime.onMessage.addListener(
      Background.messagingUtilities.messageListener,
    );
  },
  async updateSettings() {
    const os = (await chrome.runtime.getPlatformInfo()).os;
    const prefs = await chrome.storage.sync.get(Settings.prefs);
    const ver = chrome.runtime.getManifest().version;
    prefs.installed = true;
    prefs.version = ver;
    prefs.os = os;
    await chrome.storage.sync.set(prefs);
    chrome.storage.onChanged.addListener(Background.storageListener);
  },
  async setAction() {
    const os = (await chrome.runtime.getPlatformInfo()).os;
    if (os === 'android') {
      chrome.action.onClicked.addListener(tab => {
        (async () => {
          try {
            if (tab && typeof tab.id === 'number') {
              await chrome.tabs.sendMessage(tab.id, {
                action: 'video_qualitysize_change',
                ...{},
                isOptionHandle: true,
              });
            }
          } catch (e) {}
        })();
      });
    } else {
      chrome.action.setPopup({ popup: '../popup/popup.html' });
    }
  },
  async installAndUpdateCheck(reason) {
    const os = (await chrome.runtime.getPlatformInfo()).os;
    let u = Extension.domain + '/?p=';
    if (reason === 'install') {
      u += Extension.firstRunOsURLs[os] || Extension.firstRunURL;
    } else if (reason === 'update') {
      u += Extension.updateURL;
    }
    Utils.oRTCT({ url: u });
  },
  onInstalledListener(details) {
    const c = chrome.runtime.OnInstalledReason;
    switch (details.reason) {
      case c.INSTALL:
        Background.installAndUpdateCheck('install');
        break;
      case c.UPDATE:
        Background.installAndUpdateCheck('update');
        break;
      case 'browser_update':
        break;
      case c.CHROME_UPDATE:
        break;
      case c.SHARED_MODULE_UPDATE:
        break;
      default:
        break;
    }
  },
  storageListener(_changes, _area) {},
  messagingUtilities: {
    messageListener(request, sender, _sendResponse) {
      if (request.action === 'qualitysize_ask') {
        chrome.storage.sync.get(null, function (items) {
          if (sender.tab && typeof sender.tab.id === 'number') {
            chrome.tabs.sendMessage(
              sender.tab.id,
              { action: 'video_qualitysize_change', ...items },
              function () {},
            );
          }
        });
      }
      return undefined;
    },
  },
};
Background.init();
