'use strict';
const ContentScript = {
  async requestChange(options) {
    const isOptionsEmpty = Object.keys(options).length === 0;
    if (isOptionsEmpty) {
      options = await ContentScript.askForExtSettings();
    }
    ContentScript.change(options);
  },
  change(options) {
    window.postMessage(
      {
        type: 'YTHD_BY_CS_REQUEST_CHANGE',
        msgSource: 'content_script',
        id: chrome.runtime.getURL(''),
        ...options,
      },
      '*',
    );
  },
  async askForExtSettings() {
    return await chrome.storage.sync.get(null);
  },
  addPageScript() {
    const s = document.createElement('script');
    s.src = chrome.runtime.getURL('scripts/ythd.js');
    s.addEventListener('load', e => {
      const sTag = e.currentTarget;
      if (sTag && sTag instanceof HTMLElement && sTag.parentNode) {
        sTag.parentNode.removeChild(sTag);
      }
    });
    (document.head || document.documentElement).appendChild(s);
  },
  attempt() {
    ContentScript.requestChange({});
  },
  addDOMContentLoadedHandler() {
    document.addEventListener('DOMContentLoaded', _e => {
      ContentScript.requestChange({});
    });
  },
  messagingUtilities: {
    messageListener(request, _sender, _sendResponse) {
      if (request.action === 'video_qualitysize_change') {
        try {
          ContentScript.requestChange(request);
        } catch (e) {}
      }
    },
  },
  addMessageHandler() {
    window.addEventListener('message', event => {
      if (event.source !== window) return;
      switch (event.data?.type) {
        case 'FROM_PAGE':
          break;
        case 'FROM_PAGE_SCRIPT_REQUEST_CHANGE':
          ContentScript.requestChange({});
          break;
        default:
          break;
      }
    });
  },
  init() {
    ContentScript.addPageScript();
    ContentScript.addDOMContentLoadedHandler();
    chrome.runtime.onMessage.addListener(
      ContentScript.messagingUtilities.messageListener,
    );
    ContentScript.addMessageHandler();
  },
};
ContentScript.init();
