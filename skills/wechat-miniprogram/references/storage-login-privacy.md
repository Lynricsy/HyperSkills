# Storage, login and privacy

Verified against: base library 3.x, `miniprogram-api-typings` 5.2.3.

## Contents

- [Storage quotas and what storage is for](#storage-quotas-and-what-storage-is-for)
- [Login](#login)
- [What session_key is and is not](#what-session_key-is-and-is-not)
- [Authorization scopes](#authorization-scopes)
- [The refusal path](#the-refusal-path)
- [Location needs more than a scope](#location-needs-more-than-a-scope)
- [User identity: profile, phone number](#user-identity-profile-phone-number)
- [The privacy guideline gate](#the-privacy-guideline-gate)
- [Server domains](#server-domains)
- [Checklist](#checklist)

## Storage quotas and what storage is for

- **1 MB per key**, **10 MB in total**, per mini program per user.
- Data persists until the user deletes the mini program or the system reclaims space.
  It is a cache with no delivery guarantee, not a database.
- `wx.setStorage`/`wx.getStorage` are asynchronous; `wx.setStorageSync`/
  `wx.getStorageSync` block the logic thread.
- `wx.batchSetStorage`/`wx.batchGetStorage` exist for multi-key writes.

Storage is for persistence across launches. Two misuses cost real time:

```javascript
// wrong: storage as a state bus between pages
wx.setStorageSync('currentUser', user)

// right: in-memory shared state
getApp().globalData.currentUser = user
```

```javascript
// wrong: reading several keys synchronously during startup
onLaunch() {
  const a = wx.getStorageSync('a'); const b = wx.getStorageSync('b')
}

// right: read what the first screen needs, asynchronously, and defer the rest
```

Always version what you write, so a schema change does not crash on a stale value:

```javascript
const CACHE_VERSION = 3
wx.setStorage({ key: 'feed', data: { v: CACHE_VERSION, items } })
const cached = wx.getStorageSync('feed')
const items = cached && cached.v === CACHE_VERSION ? cached.items : []
```

Never store `session_key`, a server session secret, or unencrypted personal data.

## Login

```
mini program                    your server                    WeChat server
     │ wx.login()                    │                               │
     ├──── code ───────────────────► │                               │
     │                               ├── auth.code2Session ────────► │
     │                               │ ◄─ openid, unionid,           │
     │                               │    session_key ───────────────┤
     │ ◄── your own session token ───┤                               │
```

```javascript
wx.login({
  success: async ({ code }) => {
    // code is single-use and valid for five minutes
    const { token } = await postToYourServer('/session', { code })
    wx.setStorageSync('token', token)
  },
})
```

Rules that follow from this shape:

- The code is **single-use** and valid for **five minutes**. Fetching one at startup
  "to have it ready" and using it later is the standard cause of an intermittent
  `invalid code`.
- `openid` identifies the user within one mini program; `unionid` identifies them across
  everything under the same WeChat Open Platform account, and is only returned when the
  mini program is bound to one.
- `wx.checkSession()` tells you whether the WeChat session is still valid. It says
  nothing about **your** session — keep your own expiry and re-login when your token
  expires, not when `checkSession` fails.
- Never trust an `openid` sent from the client. It must come out of `code2Session` on
  your server.

## What session_key is and is not

`session_key` is the key used to decrypt and verify the encrypted payloads WeChat
returns (for example encrypted phone number data). It must stay on your server: it must
not be returned to the mini program and must not be handed to a third party. A
mini program holding `session_key` can forge any encrypted payload it wants.

## Authorization scopes

Calling a scoped API prompts the first time, succeeds silently afterwards, and goes
straight to `fail` if the user has refused. Current scopes:

| Scope | Guards |
|---|---|
| `scope.userLocation` | `wx.getLocation`, `wx.startLocationUpdate`, `MapContext.moveToLocation` |
| `scope.userFuzzyLocation` | `wx.getFuzzyLocation` |
| `scope.userLocationBackground` | `wx.startLocationUpdateBackground` |
| `scope.record` | `live-pusher`, `wx.startRecord`, `wx.joinVoIPChat`, `RecorderManager.start` |
| `scope.camera` | `camera` component, `live-pusher`, `wx.createVKSession` |
| `scope.bluetooth` | `wx.openBluetoothAdapter`, `wx.createBLEPeripheralServer` |
| `scope.writePhotosAlbum` | `wx.saveImageToPhotosAlbum`, `wx.saveVideoToPhotosAlbum` |
| `scope.addPhoneContact` | `wx.addPhoneContact` |
| `scope.addPhoneCalendar` | `wx.addPhoneCalendar`, `wx.addPhoneRepeatCalendar` |
| `scope.werun` | `wx.getWeRunData` |

`scope.address`, `scope.invoiceTitle` and `scope.invoice` no longer require
authorization — the APIs can be called directly. `scope.userInfo` has been withdrawn for
mini programs; use the avatar/nickname input components instead.

A granted or refused decision is recorded until the user deletes the mini program.

## The refusal path

Once refused, `wx.authorize` produces no dialog at all. The only recovery is the
settings sheet:

```javascript
async function ensureScope(scope) {
  const { authSetting } = await wxp(wx.getSetting)
  if (authSetting[scope]) return true
  if (authSetting[scope] === false) {
    // previously refused: a dialog will not appear, send the user to settings
    const { authSetting: after } = await wxp(wx.openSetting)
    return !!after[scope]
  }
  try { await wxp(wx.authorize, { scope }); return true } catch { return false }
}
```

Note the three states: `true` granted, `false` refused, `undefined` never asked. Code
that treats `undefined` and `false` the same either skips a prompt that would have
worked or opens the settings sheet at a user who has never been asked.

Ask at the moment the feature needs it, with the reason visible, rather than in
`onLaunch`. The authorization dialog shows the text from your privacy guideline, so that
text is user-facing.

## Location needs more than a scope

`scope.userLocation`, `scope.userFuzzyLocation` and `scope.userLocationBackground`
additionally require a purpose declaration in `app.json`:

```json
{
  "requiredPrivateInfos": ["getLocation", "chooseLocation"],
  "permission": {
    "scope.userLocation": { "desc": "用于推荐附近门店" }
  }
}
```

Missing `requiredPrivateInfos` makes the API fail on a real device while working in the
simulator. Background location also has to be declared under the background-mode
capability, and only prompts from WeChat 8.0.0.

## User identity: profile, phone number

- Avatar and nickname come from `<button open-type="chooseAvatar">` and
  `<input type="nickname">`; the old `wx.getUserInfo`/`wx.getUserProfile` path for
  obtaining profile data has been withdrawn for mini programs.
- Phone number comes from `<button open-type="getPhoneNumber">` (encrypted, decrypted
  server-side with `session_key`) or `open-type="getRealtimePhoneNumber"` (a code
  exchanged server-side). Both require the mini program to have the capability enabled.
- Anything identity-related arrives from a user gesture on a `<button>`; there is no API
  that produces it without one.

## The privacy guideline gate

An interface not declared in the mini program's privacy guideline on the platform is
**disabled**, not merely un-prompted. Declaring it is a platform-side configuration
step; the code side is a consent sync (base library 2.32.3+):

```javascript
Page({
  data: { showPrivacy: false },
  onLoad() {
    wx.getPrivacySetting({
      success: (res) => {
        // res.needAuthorization, res.privacyContractName
        if (res.needAuthorization) this.setData({ showPrivacy: true })
      },
    })
  },
  openContract() { wx.openPrivacyContract({}) },
  onAgree() { /* consent recorded by the button below; privacy APIs usable now */ },
})
```

```html
<view wx:if="{{showPrivacy}}">
  <button bindtap="openContract">查看隐私协议</button>
  <button id="agree-btn" open-type="agreePrivacyAuthorization"
          bindagreeprivacyauthorization="onAgree">同意</button>
</view>
```

The reactive alternative is `wx.onNeedPrivacyAuthorization((resolve, eventInfo) => …)`,
which fires when a privacy API is called before consent; resolve with
`{ buttonId: 'agree-btn', event: 'agree' }` or `{ event: 'disagree' }`.
`wx.requirePrivacyAuthorize` simulates a privacy API call for testing.

Two traps:

- `<input type="nickname">` does **not** raise
  `onNeedPrivacyAuthorization`; it silently degrades to `type="text"` while consent is
  missing, so a nickname field that quietly stops behaving specially means consent was
  never synced.
- Adding a new privacy interface to the guideline requires re-syncing consent for that
  interface; already-synced users keep access to the interfaces that existed before.

Consent is cleared when the user removes the mini program from the recents list, which
is also how you reset it while testing.

## Server domains

`wx.request`, `uploadFile`, `downloadFile` and sockets only reach domains registered in
the platform's server settings, over HTTPS/WSS with a valid certificate. The devtools
option that disables domain checking is a local convenience: with it on, development
works and production requests are blocked. Turn it off before believing an integration
works.

## Checklist

- [ ] `wx.login`'s code is fetched at the moment it is exchanged, not cached.
- [ ] `session_key` never leaves the server; the client holds only your own token.
- [ ] Every scoped API handles `fail`, and refusal routes through
      `wx.getSetting` + `wx.openSetting` rather than retrying `wx.authorize`.
- [ ] `authSetting[scope] === undefined` is treated as "never asked", not "refused".
- [ ] Location APIs have `requiredPrivateInfos` and a `permission` description.
- [ ] Every privacy interface used is declared in the platform's privacy guideline, and
      the consent sync is wired.
- [ ] Storage writes are versioned, under 1 MB per key, and hold no secrets.
- [ ] Domain checking is on in devtools before an integration is called done.

<!-- sources: wx-official-docs, wx-api-typings -->
