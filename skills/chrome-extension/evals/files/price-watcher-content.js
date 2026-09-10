// Registered in manifest.json as:
//   { "matches": ["https://shop.example.com/*"],
//     "js": ["price-watcher-content.js"],
//     "run_at": "document_start" }
// (no "world" key, no "web_accessible_resources" entry in the manifest)

const product = window.__PRODUCT_STATE__;
const price = product.variants[0].price;

chrome.runtime.sendMessage({ type: 'PRICE_SEEN', sku: product.sku, price });

const { watchlist } = await chrome.storage.session.get('watchlist');
if (watchlist.includes(product.sku)) {
  document.querySelector('#add-to-cart').insertAdjacentHTML(
    'afterend',
    '<span id="pw-badge">watched</span>',
  );
}

const observer = new MutationObserver(() => {
  const next = window.__PRODUCT_STATE__.variants[0].price;
  chrome.runtime.sendMessage({ type: 'PRICE_SEEN', sku: product.sku, price: next });
});
observer.observe(document.body, { childList: true, subtree: true, characterData: true });

// Read the store's own analytics helper so we can reuse its cart totals.
const helper = document.createElement('script');
helper.src = 'bridge.js';
document.documentElement.append(helper);

window.addEventListener('message', (event) => {
  chrome.runtime.sendMessage({ type: 'CART', cart: event.data });
});
