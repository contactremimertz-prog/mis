/**
 * @file Matching engine of the MIS assistant (no network, no generation).
 *
 * A typed question is reduced to keywords (lower case, no accents, no stop
 * words) and compared with the keywords and question text of every entry of
 * window.MIS_KB, in all 4 languages, so a question typed in another language
 * is still understood.
 *
 * Result of match(text):
 *   { kind: "answer", id }            one entry clearly wins
 *   { kind: "clarify", ids: [...] }   several entries are equally close
 *   { kind: "none" }                  nothing matches
 */
(function () {
  "use strict";

  const MIS = window.MIS;
  const { KB } = window.MIS_KB;
  const LANG_CODES = ["fr", "en", "es", "de"];

  /** Short words that carry no meaning for matching, all languages together. */
  const STOP = new Set(("le la les un une des du de d l et ou a au aux en dans sur pour par que qui quoi quel quelle " +
    "est sont je j me mon ma mes ce cet cette comment pourquoi peut on il elle ne pas " +
    "the a an of to in on for and or is are do does how why what which who can i my me it this that " +
    "el los las uno una unos de del y o es son como por que quien puedo mi mis este esta " +
    "der die das ein eine und oder ist sind wie warum was wer kann ich mein meine ist dies").split(" "));

  /** Lower case, accents removed, punctuation turned into spaces. */
  function fold(text) {
    return String(text || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
      .replace(/ß/g, "ss").replace(/[^a-z0-9]+/g, " ").trim();
  }

  /** Meaningful words of a text (3 letters or more, no stop words). */
  function words(text) {
    return fold(text).split(" ").filter(w => w.length >= 3 && !STOP.has(w));
  }

  /**
   * Two words match when they share a long enough beginning: at least 5
   * letters and 55 % of the longer word (plurals and verb forms match,
   * "conserver" / "conservation"; long German compounds do not).
   */
  function sameWord(a, b) {
    if (a === b) return true;
    let cp = 0;
    while (cp < a.length && cp < b.length && a[cp] === b[cp]) cp++;
    return cp >= 5 && cp >= 0.55 * Math.max(a.length, b.length);
  }

  /** Searchable words of an entry: keywords and question of every language, built once. */
  const INDEX = KB.map(entry => {
    const set = new Set();
    LANG_CODES.forEach(l => {
      words(entry[l].kw).forEach(w => set.add(w));
      words(entry[l].q).forEach(w => set.add(w));
    });
    return { id: entry.id, words: [...set] };
  });

  /** Number of query words found in the entry. */
  function score(queryWords, item) {
    return queryWords.filter(q => item.words.some(w => sameWord(q, w))).length;
  }

  /** Entry whose question, in any language, is exactly the typed text. */
  function exactQuestion(text) {
    const typed = fold(text);
    const hit = KB.find(e => LANG_CODES.some(l => fold(e[l].q) === typed));
    return hit ? hit.id : null;
  }

  /**
   * Finds the entry that answers `text`, or asks for a precision.
   * Ranking: number of matched words, then the share of the entry's words
   * matched (a short, specific entry wins over a long, general one).
   * A single matched word shared by several entries is too vague: the
   * assistant offers the closest questions instead of guessing.
   */
  function match(text) {
    const exact = exactQuestion(text);
    if (exact) return { kind: "answer", id: exact };
    const q = [...new Set(words(text))];
    if (!q.length) return { kind: "none" };
    const ranked = INDEX.map(item => {
      const s = score(q, item);
      return { id: item.id, s, share: s / item.words.length };
    }).filter(r => r.s > 0).sort((a, b) => b.s - a.s || b.share - a.share);
    if (!ranked.length) return { kind: "none" };
    const top = ranked[0];
    const same = ranked.filter(r => r.s === top.s);
    const vague = top.s === 1 && same.length > 1;
    const tied = same.filter(r => r.share === top.share).length > 1;
    if (vague || tied) return { kind: "clarify", ids: same.slice(0, 3).map(r => r.id) };
    return { kind: "answer", id: top.id };
  }

  /** Entry by id. */
  const entry = id => KB.find(e => e.id === id) || null;

  MIS.chatEngine = { match, entry, fold, words };
})();
