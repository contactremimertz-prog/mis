/**
 * @file Core utilities shared by every module.
 *
 * Creates the global `window.MIS` namespace and the shared application state,
 * then exposes small helpers: DOM lookup, HTML escaping, date arithmetic, a
 * synchronous SHA-256 used to chain the audit log, and PBKDF2 credential checks.
 *
 * Load order: this file must be loaded first (see the inline loader in index.html).
 */
(function () {
  "use strict";

  const MIS = (window.MIS = window.MIS || {});

  /**
   * Shared mutable state. Every module reads and writes it through `MIS.state`
   * so that there is a single source of truth (no hidden module globals).
   */
  MIS.state = {
    SQL: null,          // sql.js module, set at start-up
    db: null,           // current SQLite database (sql.js Database)
    me: null,           // active demo profile (a row of the `users` table)
    shaOk: null,        // SHA-256 self-test against WebCrypto: true, false or null (unavailable)
    lang: "fr",         // current UI language code
    exportSpec: null,   // table spec currently on screen, used by the CSV/PDF exports
    current: null,      // "type:id" of the open record dialog, used to refresh it after an action
    filters: { fleet: "all", wo: "active", stock: "all", nc: "open", search: "" },
    saveState: "saved", // persistence indicator: "saved", "saving" or "memory"
    lastDenied: null    // last denied screen (route + user), to log a denial only once
  };

  /** Browser storage keys. */
  MIS.KEYS = { store: "mis-demo-db-v2", lang: "mis-demo-lang" };

  /** Reference "today" for every due-date computation (fixed for the session). */
  const TODAY = new Date();

  /** Returns the first element matching a CSS selector. */
  const $ = selector => document.querySelector(selector);

  const HTML_ENTITIES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

  /** Escapes a value for safe insertion into HTML (text or attribute). */
  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => HTML_ENTITIES[c]);

  /** Formats a date as a local ISO day string (YYYY-MM-DD). */
  function isoD(date) {
    const d = new Date(date);
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return d.getFullYear() + "-" + mm + "-" + dd;
  }

  /** ISO day `n` days after TODAY (negative values go back in time). */
  function addDays(n) {
    const d = new Date(TODAY);
    d.setDate(d.getDate() + n);
    return isoD(d);
  }

  /** ISO day `months` months after the ISO day `day`. */
  function addMonths(day, months) {
    const d = new Date(day + "T00:00:00");
    d.setMonth(d.getMonth() + months);
    return isoD(d);
  }

  /** Whole days from TODAY to the ISO day `day` (negative when in the past). */
  function daysTo(day) {
    const target = new Date(day + "T00:00:00");
    const today = new Date(isoD(TODAY) + "T00:00:00");
    return Math.round((target - today) / 86400000);
  }

  /* ---------------------------------------------------------
     SHA-256 (FIPS 180-4)
     A synchronous implementation is needed because log entries are
     written inside SQL transactions. It is checked at start-up against
     WebCrypto (see selfTestSha).
     --------------------------------------------------------- */
  const SHA_K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];
  const SHA_H0 = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
  const rotr = (x, n) => (x >>> n) | (x << (32 - n));

  /** Pads the message bytes and packs them into 32-bit big-endian words. */
  function shaPad(bytes) {
    const len = bytes.length;
    const nBlocks = (len + 9 + 63) >> 6;
    const words = new Uint32Array(nBlocks * 16);
    for (let i = 0; i < len; i++) words[i >> 2] |= bytes[i] << (24 - (i % 4) * 8);
    words[len >> 2] |= 0x80 << (24 - (len % 4) * 8);
    words[nBlocks * 16 - 1] = len * 8;
    words[nBlocks * 16 - 2] = Math.floor(len / 0x20000000);
    return { words, nBlocks };
  }

  /** Processes one 512-bit block and returns the new hash state. */
  function shaBlock(H, words, block, W) {
    for (let i = 0; i < 16; i++) W[i] = words[block * 16 + i];
    for (let i = 16; i < 64; i++) {
      const s0 = rotr(W[i - 15], 7) ^ rotr(W[i - 15], 18) ^ (W[i - 15] >>> 3);
      const s1 = rotr(W[i - 2], 17) ^ rotr(W[i - 2], 19) ^ (W[i - 2] >>> 10);
      W[i] = (W[i - 16] + s0 + W[i - 7] + s1) | 0;
    }
    let [a, b, c, d, e, f, g, h] = H;
    for (let i = 0; i < 64; i++) {
      const t1 = (h + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + SHA_K[i] + W[i]) | 0;
      const t2 = ((rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) | 0;
      h = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0;
    }
    return [H[0] + a, H[1] + b, H[2] + c, H[3] + d, H[4] + e, H[5] + f, H[6] + g, H[7] + h].map(x => x | 0);
  }

  /** SHA-256 of a byte array, as a 32-byte Uint8Array. */
  function sha256Bytes(bytes) {
    const { words, nBlocks } = shaPad(bytes);
    const W = new Uint32Array(64);
    let H = SHA_H0.slice();
    for (let b = 0; b < nBlocks; b++) H = shaBlock(H, words, b, W);
    const out = new Uint8Array(32);
    H.forEach((x, i) => { out[i * 4] = x >>> 24; out[i * 4 + 1] = (x >>> 16) & 255; out[i * 4 + 2] = (x >>> 8) & 255; out[i * 4 + 3] = x & 255; });
    return out;
  }

  const utf8 = str => new TextEncoder().encode(str);
  const toHex = bytes => [...bytes].map(b => b.toString(16).padStart(2, "0")).join("");
  const fromHex = hex => new Uint8Array(hex.match(/../g).map(h => parseInt(h, 16)));

  /** SHA-256 of a string (UTF-8), as 64 lowercase hex characters. */
  const sha256 = str => toHex(sha256Bytes(utf8(str)));

  /* ---------------------------------------------------------
     Credentials: PBKDF2-HMAC-SHA256
     Authorisation numbers are never stored in clear: the database keeps
     "pbkdf2-sha256$<iterations>$<salt hex>$<hash hex>". Verification uses
     WebCrypto when available, else the synchronous fallback below.
     --------------------------------------------------------- */

  /** HMAC-SHA256 (RFC 2104) on byte arrays. */
  function hmacSha256(key, message) {
    let k = key.length > 64 ? sha256Bytes(key) : key;
    const block = new Uint8Array(64);
    block.set(k);
    const inner = new Uint8Array(64 + message.length), outer = new Uint8Array(64 + 32);
    for (let i = 0; i < 64; i++) { inner[i] = block[i] ^ 0x36; outer[i] = block[i] ^ 0x5c; }
    inner.set(message, 64);
    outer.set(sha256Bytes(inner), 64);
    return sha256Bytes(outer);
  }

  /** PBKDF2-HMAC-SHA256 (RFC 8018), one 32-byte block, synchronous fallback. */
  function pbkdf2Sync(password, salt, iterations) {
    const key = utf8(password);
    const first = new Uint8Array(salt.length + 4);
    first.set(salt);
    first[salt.length + 3] = 1; // block index 1, big-endian
    let u = hmacSha256(key, first);
    const out = u.slice();
    for (let i = 1; i < iterations; i++) {
      u = hmacSha256(key, u);
      for (let j = 0; j < 32; j++) out[j] ^= u[j];
    }
    return out;
  }

  /** PBKDF2-HMAC-SHA256 with WebCrypto, falling back to pbkdf2Sync(). Returns hex. */
  async function pbkdf2(password, saltHex, iterations) {
    const salt = fromHex(saltHex);
    try {
      const key = await crypto.subtle.importKey("raw", utf8(password), "PBKDF2", false, ["deriveBits"]);
      const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt, iterations }, key, 256);
      return toHex(new Uint8Array(bits));
    } catch (e) {
      return toHex(pbkdf2Sync(password, salt, iterations));
    }
  }

  /** Constant-time comparison of two hex strings. */
  function sameHex(a, b) {
    if (a.length !== b.length) return false;
    let diff = 0;
    for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
    return diff === 0;
  }

  /**
   * Checks a typed secret against a stored "pbkdf2-sha256$iter$salt$hash" value.
   * @returns {Promise<boolean>}
   */
  async function verifySecret(stored, typed) {
    const parts = String(stored || "").split("$");
    if (parts.length !== 4 || parts[0] !== "pbkdf2-sha256") return false;
    const iterations = parseInt(parts[1], 10);
    if (!(iterations >= 10000)) return false;
    return sameHex(await pbkdf2(typed, parts[2], iterations), parts[3]);
  }

  /** Previous-hash value of the first audit log entry. */
  const GENESIS = "0".repeat(64);

  /**
   * Checks sha256() against WebCrypto.
   * @returns {Promise<boolean|null>} true if identical, false if different, null if WebCrypto is unavailable.
   */
  async function selfTestSha() {
    const sample = "MIS-démo-é";
    try {
      const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(sample));
      const hex = [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, "0")).join("");
      return hex === sha256(sample);
    } catch (e) {
      return null;
    }
  }

  Object.assign(MIS, { $, esc, TODAY, isoD, addDays, addMonths, daysTo, sha256, selfTestSha, GENESIS, verifySecret, pbkdf2Sync, toHex, fromHex });
})();
