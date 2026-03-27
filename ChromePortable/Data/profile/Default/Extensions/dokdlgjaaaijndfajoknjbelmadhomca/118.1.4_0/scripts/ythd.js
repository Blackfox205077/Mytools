'use strict';
const YouTubeHighDefinition = {
  ytPlayer: null,
  $: selector => document.querySelector(selector),
  requestChange(options) {
    if (/^(www\.)?youtube\.com$/.test(window.location.hostname)) {
      YouTubeHighDefinition.changeVideoPlayer(options);
      YouTubeHighDefinition.changeVideoSize(options);
      YouTubeHighDefinition.expandVideoDescription(options);
      YouTubeHighDefinition.enablesuggestedautoplay(options);
    } else if (
      /^(www\.)?youtube-nocookie\.com$/.test(window.location.hostname)
    ) {
      YouTubeHighDefinition.changeVideoPlayer(options);
    }
  },
  changeVideoPlayer({
    subtitles,
    video_quality = 'highres',
    video_speed,
    volume,
    volumelevel,
    youtubevideoautoplaybehavior,
  }) {
    const $ = YouTubeHighDefinition.$;
    const pN = window.location.pathname;
    const isEmbed = pN.startsWith('/embed');
    if (pN === '/watch' || isEmbed) {
      const player = $('#movie_player');
      const enableautoplay =
        YouTubeHighDefinition.getYoutubeVideoAutoPlayBehavior(
          youtubevideoautoplaybehavior,
        );
      const vol_level = YouTubeHighDefinition.getVolumeLevel(
        volume,
        volumelevel,
      );
      const ythdinterval = window.setInterval(() => {
        if (player && YouTubeHighDefinition.checkPlayerReady(player)) {
          if (volume !== 'default') {
            player.unMute();
            player.setVolume(vol_level);
          }
          if (video_quality !== 'default') {
            player.setPlaybackQualityRange(video_quality, video_quality);
          }
          player.setPlaybackRate(parseInt(video_speed));
          const sbtBut = $('.ytp-subtitles-button');
          if (subtitles === 'on') {
            if (
              sbtBut &&
              sbtBut instanceof HTMLElement &&
              sbtBut.getAttribute('aria-pressed') === 'false'
            ) {
              player.toggleSubtitlesOn();
              if (sbtBut.getAttribute('aria-pressed') === 'false') {
                setTimeout(() => {
                  if (sbtBut.getAttribute('aria-pressed') === 'false') {
                    player.toggleSubtitlesOn();
                  }
                }, 1000);
              }
            }
          } else if (subtitles === 'off') {
            if (sbtBut && sbtBut.getAttribute('aria-pressed') === 'true') {
              player.toggleSubtitles();
            }
          }
          window.clearInterval(ythdinterval);
        }
      }, 50);
    }
  },
  getYoutubeVideoAutoPlayBehavior(youtubevideoautoplaybehavior) {
    switch (youtubevideoautoplaybehavior) {
      case 'default':
        return true;
      case 'autoplay':
        return true;
      case 'autopause':
        return false;
      default:
        break;
    }
  },
  getVolumeLevel: (volume, volumelevel) => {
    switch (volume) {
      case 'default':
        return parseInt(volumelevel);
      case 'mute':
        return 0;
      case '100':
        return 100;
      case 'volumelevel':
        return parseInt(volumelevel);
      default:
        return parseInt(volumelevel);
    }
  },
  checkPlayerReady(player) {
    try {
      if (player.getPlayerState() !== -1) return true;
      else return false;
    } catch (e) {
      return false;
    }
  },
  changeVideoSize({ id, video_size = 'expand', isOptionHandle }) {
    const $ = YouTubeHighDefinition.$;
    const channel = $('#playnav-player');
    if (channel) return;
    if (video_size === 'fullpage') {
      YouTubeHighDefinition.addStyles(id);
      YouTubeHighDefinition.handleSizeButton('expand');
      YouTubeHighDefinition.createMutationObserver(video_size, id);
    } else if (video_size === 'expand') {
      YouTubeHighDefinition.removeStyles();
      YouTubeHighDefinition.handleSizeButton('expand');
      YouTubeHighDefinition.createMutationObserver(video_size, id);
      if (isOptionHandle) {
        window.scrollTo(0, 0);
      }
    } else if (video_size === 'shrink') {
      YouTubeHighDefinition.removeStyles();
      YouTubeHighDefinition.handleSizeButton('shrink');
      YouTubeHighDefinition.createMutationObserver(video_size, id);
      if (isOptionHandle) {
        window.scrollTo(0, 0);
      }
    }
  },
  addStyles(id) {
    if (window.location.pathname !== '/watch') return;
    const $ = YouTubeHighDefinition.$;
    if (id && !$('#ythdlink')) {
      let link = document.createElement('link');
      link.setAttribute('rel', 'stylesheet');
      link.setAttribute('type', 'text/css');
      link.setAttribute('id', 'ythdlink');
      link.setAttribute('href', id + 'style/style.css');
      document.head.appendChild(link);
    }
    const fbc = $('#full-bleed-container');
    const pfbc = $('#player-full-bleed-container');
    if (fbc && fbc instanceof HTMLElement) {
      fbc.style.height = window.innerHeight + 'px';
      fbc.style.maxHeight = 'unset';
    }
    if (pfbc && pfbc instanceof HTMLElement) {
      pfbc.style.height = window.innerHeight + 'px';
    }
    const pm = $('#page-manager');
    const mc = $('#masthead-container');
    const mp = $('#movie_player');
    if (
      pm &&
      pm instanceof HTMLElement &&
      mc &&
      mc instanceof HTMLElement &&
      mp
    ) {
      mc.style.position = 'static';
      pm.style.marginTop = '0';
      window.setTimeout(() => {
        if (mp) {
          mp.scrollIntoView(false);
        }
      }, 1500);
    }
  },
  removeStyles() {
    const $ = YouTubeHighDefinition.$;
    const s1 = $('#ythdlink');
    s1?.parentNode?.removeChild(s1);
    const s2 = $('#ythdlink-2');
    s2?.parentNode?.removeChild(s2);
    const fbc = $('#full-bleed-container');
    const pfbc = $('#player-full-bleed-container');
    const mc = $('#masthead-container');
    const pm = $('#page-manager');
    fbc && fbc instanceof HTMLElement && (fbc.style.height = '');
    fbc && fbc instanceof HTMLElement && (fbc.style.maxHeight = '');
    pfbc && pfbc instanceof HTMLElement && (pfbc.style.height = '');
    mc && mc instanceof HTMLElement && (mc.style.position = '');
    pm && pm instanceof HTMLElement && (pm.style.marginTop = '');
  },
  findPosition(node) {
    let left_pos, top_pos;
    left_pos = top_pos = 0;
    if (node.offsetParent) {
      do {
        left_pos += node.offsetLeft;
        top_pos += node.offsetTop;
      } while (
        node.offsetParent instanceof HTMLElement &&
        (node = node.offsetParent)
      );
    }
    return [left_pos, top_pos];
  },
  createMutationObserver(video_size, id) {
    const observer = new window.MutationObserver(mutationsList => {
      YouTubeHighDefinition.handleMutation(mutationsList, video_size, id);
    });
    const config = { childList: true, subtree: true };
    observer.observe(document, config);
  },
  handleMutation(mutationsList, video_size, id) {
    for (let mutation of mutationsList) {
      if (mutation.type === 'childList') {
        for (let node of mutation.addedNodes) {
          if (node instanceof HTMLElement) {
            if (
              video_size === 'fullpage' &&
              node.id === 'full-bleed-container'
            ) {
              YouTubeHighDefinition.addStyles(id);
            }
            if (node.nodeName === 'YTD-TOPBAR-MENU-BUTTON-RENDERER') {
              switch (video_size) {
                case 'fullpage':
                  YouTubeHighDefinition.handleSizeButton('expand');
                  break;
                case 'expand':
                  YouTubeHighDefinition.handleSizeButton('expand');
                  break;
                case 'shrink':
                  YouTubeHighDefinition.handleSizeButton('shrink');
                  break;
              }
            }
          }
        }
      }
    }
  },
  handleSizeButton(video_size) {
    if (document.location.pathname !== '/watch') return;
    const $ = YouTubeHighDefinition.$;
    const size_path = $('.ytp-size-button path');
    if (size_path) {
      const theater = $('ytd-watch[theater]');
      const searchVal = video_size === 'expand' ? 'm 28,' : 'm 26,';
      const theaterBool = video_size === 'expand' ? !theater : theater;
      const isClickable = size_path.getAttribute('d')?.indexOf(searchVal) === 0;
      if ((size_path && isClickable) || theaterBool) {
        if (size_path && isClickable && size_path.parentNode) {
          const sB = size_path.parentNode.parentNode;
          if (sB && sB instanceof HTMLElement) {
            sB.click();
          }
        }
      }
    }
  },
  expandVideoDescription({ autoexpanddescription, isOptionHandle }) {
    if (document.location.pathname !== '/watch') return;
    const $ = YouTubeHighDefinition.$;
    const isMobile = window.location.host === 'm.youtube.com';
    const exBut = $(
      !isMobile ? '#expand' : '.slim-video-information-show-more',
    );
    if (autoexpanddescription) {
      if (exBut) {
        if (exBut instanceof HTMLElement) exBut.click();
      } else {
        let interval;
        interval = window.setInterval(() => {
          const exBut = $(
            !isMobile ? '#expand' : '.slim-video-information-show-more',
          );
          if (exBut) {
            if (exBut instanceof HTMLElement) exBut.click();
            window.clearInterval(interval);
          }
        }, 500);
      }
    } else {
      if (isOptionHandle) {
        const cBut = $('#collapse');
        if (cBut && cBut instanceof HTMLElement) {
          cBut.click();
        }
      }
    }
  },
  enablesuggestedautoplay({ suggestedautoplay }) {
    const $ = YouTubeHighDefinition.$;
    if (document.location.pathname.search(/^\/watch/) === 0) {
      const ac = $('#autoplay-checkbox');
      if (ac && ac instanceof HTMLInputElement) {
        ac.click();
        ac.checked = suggestedautoplay;
      }
      const tB = $(
        'paper-toggle-button#toggle[aria-pressed*=' + !suggestedautoplay + ']',
      );
      if (tB && tB instanceof HTMLElement) {
        tB.click();
      }
    }
  },
  onSPFDone: _e => {
    window.postMessage(
      {
        type: 'FROM_PAGE_SCRIPT_REQUEST_CHANGE',
        msgSource: 'ythd_script',
        text: 'NULL',
      },
      '*',
    );
  },
  handleChannelChange(event) {
    if (
      event.target &&
      event.target instanceof HTMLElement &&
      event.target.nodeName === 'EMBED'
    ) {
      window.setTimeout(function () {}, 1);
    }
  },
};
window.addEventListener('load', () => {});
window.addEventListener('spfdone', YouTubeHighDefinition.onSPFDone);
window.addEventListener('yt-navigate-start', YouTubeHighDefinition.onSPFDone);
window.addEventListener('yt-navigate-finish', () => {});
window.addEventListener('message', function (event) {
  if (event.source !== window) return;
  switch (event.data?.type) {
    case 'YTHD_BY_CS_REQUEST_CHANGE':
      YouTubeHighDefinition.requestChange({ ...event.data });
      break;
    default:
      break;
  }
});
if (window.onYouTubePlayerReady) window.onYouTubePlayerReady === null;
let onYouTubePlayerReady = function (_player) {};
window.onYouTubePlayerReady = onYouTubePlayerReady;
