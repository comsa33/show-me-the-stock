/**
 * Browser and WebView detection utilities
 */

export const isWebView = (): boolean => {
  const userAgent = navigator.userAgent.toLowerCase();
  
  // Check for common WebView indicators
  const webViewIndicators = [
    'wv',
    'webview',
    'android.*applewebkit',
    'iphone.*applewebkit.*(?!.*safari)',
    'ipod.*applewebkit.*(?!.*safari)',
    'ipad.*applewebkit.*(?!.*safari)',
  ];
  
  return webViewIndicators.some(indicator => 
    new RegExp(indicator).test(userAgent)
  );
};

export const isKakaoTalk = (): boolean => {
  return /KAKAOTALK/i.test(navigator.userAgent);
};

export const isInstagram = (): boolean => {
  return /Instagram/i.test(navigator.userAgent);
};

export const isFacebookApp = (): boolean => {
  return /FBAN|FBAV/i.test(navigator.userAgent);
};

export const isInAppBrowser = (): boolean => {
  return isWebView() || isKakaoTalk() || isInstagram() || isFacebookApp();
};

export const isMobile = (): boolean => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

export const openInExternalBrowser = (url: string) => {
  if (isKakaoTalk()) {
    // KakaoTalk specific handling
    window.location.href = `kakaotalk://web/openExternal?url=${encodeURIComponent(url)}`;
  } else {
    // General approach - try to open in system browser
    window.open(url, '_system');
  }
};