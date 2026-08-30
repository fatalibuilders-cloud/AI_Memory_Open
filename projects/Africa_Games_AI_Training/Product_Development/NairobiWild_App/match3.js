/*
 * Market Day — match-3 engine
 *
 * Pure, dependency-free. Shared by the browser UI (index.html) and the Node
 * test suite (match3.test.mjs). All randomness goes through an injectable RNG
 * so tests are deterministic.
 *
 * Board: flat array, row-major, ROWS*COLS.
 *   Cell = null (hole, mid-cascade) | { c: colorIndex, s: special|null }
 *   special: 'row' | 'col' | 'bomb' | 'rainbow'
 *
 * A move is resolved into an ordered list of PHASES, each a snapshot the UI
 * animates in turn (clear → gravity → refill → cascade again). The UI never
 * re-derives rules; it just plays back phases.
 */
(function (global) {
  'use strict';

  const ROWS = 8;
  const COLS = 8;
  const COLORS = 6;
  const BASE_POINTS = 60;
  const MAX_CASCADES = 40; // safety valve

  const SPECIAL = { ROW: 'row', COL: 'col', BOMB: 'bomb', RAINBOW: 'rainbow' };

  /* Deterministic RNG so tests (and future replays) reproduce exactly. */
  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  const idx = (r, c, cols) => r * cols + c;
  const rowOf = (i, cols) => Math.floor(i / cols);
  const colOf = (i, cols) => i % cols;

  function cloneBoard(board) {
    return board.map((t) => (t ? { c: t.c, s: t.s } : null));
  }

  /* ---------------- Match detection ---------------- */

  /*
   * Every maximal horizontal/vertical run of 3+ same-coloured tiles.
   * Returns [{ dir:'h'|'v', color, cells:[i,...] }]
   */
  function findRuns(board, rows, cols) {
    const runs = [];

    const scan = (dir, outer, inner, at) => {
      for (let o = 0; o < outer; o += 1) {
        let start = 0;
        for (let k = 1; k <= inner; k += 1) {
          const a = board[at(o, start)];
          const b = k < inner ? board[at(o, k)] : null;
          const same = a && b && a.c === b.c;
          if (!same) {
            if (k - start >= 3 && a) {
              const cells = [];
              for (let j = start; j < k; j += 1) cells.push(at(o, j));
              runs.push({ dir, color: a.c, cells });
            }
            start = k;
          }
        }
      }
    };

    scan('h', rows, cols, (r, c) => idx(r, c, cols));
    scan('v', cols, rows, (c, r) => idx(r, c, cols));
    return runs;
  }

  /*
   * Merge overlapping runs into groups. A group that contains both an
   * h-run and a v-run is an L/T shape.
   * Returns [{ color, cells:Set, maxRun, crossed }]
   */
  function findGroups(board, rows, cols) {
    const runs = findRuns(board, rows, cols);
    const groups = [];

    runs.forEach((run) => {
      const hits = groups.filter(
        (g) => g.color === run.color && run.cells.some((i) => g.cells.has(i))
      );
      if (hits.length === 0) {
        groups.push({
          color: run.color,
          cells: new Set(run.cells),
          maxRun: run.cells.length,
          dirs: new Set([run.dir]),
        });
        return;
      }
      // Merge this run and every group it bridges into the first one.
      const target = hits[0];
      run.cells.forEach((i) => target.cells.add(i));
      target.maxRun = Math.max(target.maxRun, run.cells.length);
      target.dirs.add(run.dir);
      for (let k = 1; k < hits.length; k += 1) {
        hits[k].cells.forEach((i) => target.cells.add(i));
        target.maxRun = Math.max(target.maxRun, hits[k].maxRun);
        hits[k].dirs.forEach((d) => target.dirs.add(d));
        groups.splice(groups.indexOf(hits[k]), 1);
      }
    });

    return groups.map((g) => ({
      color: g.color,
      cells: g.cells,
      maxRun: g.maxRun,
      crossed: g.dirs.size > 1,
      dir: g.dirs.has('h') ? 'h' : 'v',
    }));
  }

  function hasMatch(board, rows, cols) {
    return findRuns(board, rows, cols).length > 0;
  }

  /* Which special (if any) a group earns. */
  function specialFor(group) {
    if (group.crossed) return SPECIAL.BOMB;
    if (group.maxRun >= 5) return SPECIAL.RAINBOW;
    if (group.maxRun === 4) return group.dir === 'h' ? SPECIAL.ROW : SPECIAL.COL;
    return null;
  }

  /* ---------------- Clearing ---------------- */

  /*
   * Expand a set of seed cells through any specials they contain, so a
   * striped tile takes its row with it and a bomb takes its neighbours.
   */
  function expandClears(board, rows, cols, seeds) {
    const out = new Set();
    const queue = Array.from(seeds);
    while (queue.length > 0) {
      const i = queue.pop();
      if (out.has(i)) continue;
      const t = board[i];
      if (!t) continue;
      out.add(i);
      const r = rowOf(i, cols);
      const c = colOf(i, cols);
      if (t.s === SPECIAL.ROW) {
        for (let k = 0; k < cols; k += 1) queue.push(idx(r, k, cols));
      } else if (t.s === SPECIAL.COL) {
        for (let k = 0; k < rows; k += 1) queue.push(idx(k, c, cols));
      } else if (t.s === SPECIAL.BOMB) {
        for (let dr = -1; dr <= 1; dr += 1) {
          for (let dc = -1; dc <= 1; dc += 1) {
            const nr = r + dr;
            const nc = c + dc;
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) queue.push(idx(nr, nc, cols));
          }
        }
      } else if (t.s === SPECIAL.RAINBOW) {
        // Caught in a cascade: takes its own colour with it.
        for (let k = 0; k < board.length; k += 1) {
          if (board[k] && board[k].c === t.c) queue.push(k);
        }
      }
    }
    return out;
  }

  /* Drop tiles into holes, then refill the top from the RNG. */
  function collapse(board, rows, cols, colors, rng) {
    for (let c = 0; c < cols; c += 1) {
      let write = rows - 1;
      for (let r = rows - 1; r >= 0; r -= 1) {
        const t = board[idx(r, c, cols)];
        if (t) {
          board[idx(write, c, cols)] = t;
          if (write !== r) board[idx(r, c, cols)] = null;
          write -= 1;
        }
      }
      for (let r = write; r >= 0; r -= 1) {
        board[idx(r, c, cols)] = { c: Math.floor(rng() * colors), s: null };
      }
    }
    return board;
  }

  /* ---------------- Board creation ---------------- */

  function fillBoard(rows, cols, colors, rng) {
    const board = new Array(rows * cols).fill(null);
    for (let r = 0; r < rows; r += 1) {
      for (let c = 0; c < cols; c += 1) {
        const banned = new Set();
        if (c >= 2) {
          const a = board[idx(r, c - 1, cols)];
          const b = board[idx(r, c - 2, cols)];
          if (a && b && a.c === b.c) banned.add(a.c);
        }
        if (r >= 2) {
          const a = board[idx(r - 1, c, cols)];
          const b = board[idx(r - 2, c, cols)];
          if (a && b && a.c === b.c) banned.add(a.c);
        }
        let color = Math.floor(rng() * colors);
        let guard = 0;
        while (banned.has(color) && guard < 50) {
          color = Math.floor(rng() * colors);
          guard += 1;
        }
        board[idx(r, c, cols)] = { c: color, s: null };
      }
    }
    return board;
  }

  /* Is there any swap that would create a match? */
  function hasMove(board, rows, cols) {
    for (let r = 0; r < rows; r += 1) {
      for (let c = 0; c < cols; c += 1) {
        const i = idx(r, c, cols);
        if (board[i] && board[i].s === SPECIAL.RAINBOW) return true;
        for (const [dr, dc] of [[0, 1], [1, 0]]) {
          const nr = r + dr;
          const nc = c + dc;
          if (nr >= rows || nc >= cols) continue;
          const j = idx(nr, nc, cols);
          const copy = board.slice();
          const tmp = copy[i];
          copy[i] = copy[j];
          copy[j] = tmp;
          if (hasMatch(copy, rows, cols)) return true;
        }
      }
    }
    return false;
  }

  function newBoard(rows, cols, colors, rng) {
    let board = fillBoard(rows, cols, colors, rng);
    let guard = 0;
    while (!hasMove(board, rows, cols) && guard < 100) {
      board = fillBoard(rows, cols, colors, rng);
      guard += 1;
    }
    return board;
  }

  /* ---------------- Game state ---------------- */

  function newGame(level, seed) {
    const rng = mulberry32(seed === undefined ? (Math.random() * 1e9) | 0 : seed);
    const rows = ROWS;
    const cols = COLS;
    return {
      rows,
      cols,
      colors: COLORS,
      board: newBoard(rows, cols, COLORS, rng),
      rng,
      level,
      movesLeft: level.moves,
      score: 0,
      // collected[colorIndex] — drives "collect N mangoes" goals
      collected: new Array(COLORS).fill(0),
      over: false,
      won: false,
    };
  }

  function goalsMet(state) {
    if (state.score < state.level.target) return false;
    const collect = state.level.collect || [];
    return collect.every((g) => state.collected[g.c] >= g.n);
  }

  function starsFor(state) {
    const t = state.level.target;
    if (state.score >= Math.round(t * 1.9)) return 3;
    if (state.score >= Math.round(t * 1.4)) return 2;
    return 1;
  }

  function adjacent(a, b, cols) {
    const dr = Math.abs(rowOf(a, cols) - rowOf(b, cols));
    const dc = Math.abs(colOf(a, cols) - colOf(b, cols));
    return dr + dc === 1;
  }

  /*
   * Resolve a player swap into animation phases.
   * Returns { valid, phases, state }. On an invalid swap the state is
   * untouched and phases is empty (the UI shows a shake).
   *
   * Phase shape:
   *   { cleared:[i], created:[{i,s,c}], gained, combo, board, shuffled }
   */
  function resolveMove(state, a, b) {
    const { rows, cols, colors } = state;
    if (state.over || !adjacent(a, b, cols)) return { valid: false, phases: [], state };

    const board = cloneBoard(state.board);
    const ta = board[a];
    const tb = board[b];
    if (!ta || !tb) return { valid: false, phases: [], state };

    const phases = [];
    let score = 0;
    const collected = state.collected.slice();
    let seeds = null;

    // Rainbow swaps don't need a match to be legal.
    const aRain = ta.s === SPECIAL.RAINBOW;
    const bRain = tb.s === SPECIAL.RAINBOW;
    if (aRain || bRain) {
      seeds = new Set([a, b]);
      if (aRain && bRain) {
        for (let i = 0; i < board.length; i += 1) seeds.add(i); // clear the stall
      } else {
        const targetColor = aRain ? tb.c : ta.c;
        for (let i = 0; i < board.length; i += 1) {
          if (board[i] && board[i].c === targetColor) seeds.add(i);
        }
      }
    } else {
      board[a] = tb;
      board[b] = ta;
      if (!hasMatch(board, rows, cols)) return { valid: false, phases: [], state };
    }

    let combo = 0;
    while (combo < MAX_CASCADES) {
      let clears;
      const created = [];

      if (seeds) {
        clears = expandClears(board, rows, cols, seeds);
        seeds = null;
      } else {
        const groups = findGroups(board, rows, cols);
        if (groups.length === 0) break;

        const seedSet = new Set();
        groups.forEach((g) => g.cells.forEach((i) => seedSet.add(i)));
        clears = expandClears(board, rows, cols, seedSet);

        // A group that earns a special keeps one cell, which becomes it.
        groups.forEach((g) => {
          const s = specialFor(g);
          if (!s) return;
          const cells = Array.from(g.cells);
          const anchor = cells.includes(a) ? a : cells.includes(b) ? b : cells[Math.floor(cells.length / 2)];
          clears.delete(anchor);
          created.push({ i: anchor, s, c: g.color });
        });
      }

      if (clears.size === 0) break;

      combo += 1;
      const gained = clears.size * BASE_POINTS * combo;
      score += gained;

      const clearedList = [];
      clears.forEach((i) => {
        if (board[i]) collected[board[i].c] += 1;
        clearedList.push(i);
        board[i] = null;
      });
      created.forEach((cr) => { board[cr.i] = { c: cr.c, s: cr.s }; });

      collapse(board, rows, cols, colors, state.rng);
      phases.push({
        cleared: clearedList,
        created,
        gained,
        combo,
        board: cloneBoard(board),
        shuffled: false,
      });
    }

    // Deadlocked board: reshuffle rather than strand the player.
    let guard = 0;
    while (!hasMove(board, rows, cols) && guard < 50) {
      const shuffled = newBoard(rows, cols, colors, state.rng);
      for (let i = 0; i < board.length; i += 1) board[i] = shuffled[i];
      phases.push({ cleared: [], created: [], gained: 0, combo: 0, board: cloneBoard(board), shuffled: true });
      guard += 1;
    }

    const next = {
      ...state,
      board,
      score: state.score + score,
      collected,
      movesLeft: state.movesLeft - 1,
    };
    next.won = goalsMet(next);
    next.over = next.won || next.movesLeft <= 0;

    return { valid: true, phases, state: next };
  }

  /* ---------------- Boosters ---------------- */

  /*
   * 'hammer'  — remove one tile
   * 'shuffle' — reshuffle the board (costs no move)
   * Returns { valid, phases, state }; boosters never consume a move.
   */
  function useBooster(state, kind, target) {
    const { rows, cols, colors } = state;
    if (state.over) return { valid: false, phases: [], state };
    const board = cloneBoard(state.board);
    const phases = [];
    const collected = state.collected.slice();
    let score = 0;

    if (kind === 'hammer') {
      if (target === undefined || !board[target]) return { valid: false, phases: [], state };
      const clears = expandClears(board, rows, cols, new Set([target]));
      const clearedList = [];
      clears.forEach((i) => {
        if (board[i]) collected[board[i].c] += 1;
        clearedList.push(i);
        board[i] = null;
      });
      score += clears.size * BASE_POINTS;
      collapse(board, rows, cols, colors, state.rng);
      phases.push({ cleared: clearedList, created: [], gained: score, combo: 1, board: cloneBoard(board), shuffled: false });
    } else if (kind === 'shuffle') {
      const shuffled = newBoard(rows, cols, colors, state.rng);
      for (let i = 0; i < board.length; i += 1) board[i] = shuffled[i];
      phases.push({ cleared: [], created: [], gained: 0, combo: 0, board: cloneBoard(board), shuffled: true });
    } else {
      return { valid: false, phases: [], state };
    }

    // A booster can leave live matches on the board — settle them.
    let combo = 1;
    while (combo < MAX_CASCADES) {
      const groups = findGroups(board, rows, cols);
      if (groups.length === 0) break;
      const seedSet = new Set();
      groups.forEach((g) => g.cells.forEach((i) => seedSet.add(i)));
      const clears = expandClears(board, rows, cols, seedSet);
      const created = [];
      groups.forEach((g) => {
        const s = specialFor(g);
        if (!s) return;
        const cells = Array.from(g.cells);
        const anchor = cells[Math.floor(cells.length / 2)];
        clears.delete(anchor);
        created.push({ i: anchor, s, c: g.color });
      });
      if (clears.size === 0) break;
      combo += 1;
      const gained = clears.size * BASE_POINTS * combo;
      score += gained;
      const clearedList = [];
      clears.forEach((i) => {
        if (board[i]) collected[board[i].c] += 1;
        clearedList.push(i);
        board[i] = null;
      });
      created.forEach((cr) => { board[cr.i] = { c: cr.c, s: cr.s }; });
      collapse(board, rows, cols, colors, state.rng);
      phases.push({ cleared: clearedList, created, gained, combo, board: cloneBoard(board), shuffled: false });
    }

    const next = { ...state, board, score: state.score + score, collected };
    next.won = goalsMet(next);
    next.over = next.won || next.movesLeft <= 0;
    return { valid: true, phases, state: next };
  }

  /* ---------------- Levels ----------------
   * A journey out of Nairobi and across Kenya. Difficulty ramps by squeezing
   * moves against the target, then by adding collect goals the player can't
   * reach on score alone.
   *
   * Colour index → animal (names live in the UI):
   *   0 Simba (lion) · 1 Tembo (elephant) · 2 Punda Milia (zebra)
   *   3 Twiga (giraffe) · 4 Kifaru (rhino) · 5 Chui (leopard)
   * Goals are matched to the animal each place is actually known for.
   */
  const LEVELS = [
    { n: 1,  moves: 25, target: 1500,  collect: [],                                 blurb: 'Nairobi National Park' },
    { n: 2,  moves: 24, target: 2500,  collect: [],                                 blurb: 'Karura Forest' },
    { n: 3,  moves: 22, target: 3000,  collect: [{ c: 2, n: 15 }],                  blurb: 'Athi Plains' },
    { n: 4,  moves: 22, target: 4000,  collect: [{ c: 5, n: 18 }],                  blurb: 'Nairobi River' },
    { n: 5,  moves: 20, target: 5000,  collect: [{ c: 3, n: 20 }],                  blurb: 'Ngong Hills' },
    { n: 6,  moves: 20, target: 6000,  collect: [{ c: 1, n: 18 }],                  blurb: 'Amboseli' },
    { n: 7,  moves: 18, target: 7000,  collect: [{ c: 4, n: 20 }],                  blurb: 'Lake Nakuru' },
    { n: 8,  moves: 18, target: 8500,  collect: [{ c: 2, n: 20 }],                  blurb: "Hell's Gate" },
    { n: 9,  moves: 18, target: 9500,  collect: [{ c: 0, n: 18 }, { c: 1, n: 18 }], blurb: 'Tsavo East' },
    { n: 10, moves: 16, target: 11000, collect: [{ c: 3, n: 22 }],                  blurb: 'Samburu' },
    { n: 11, moves: 16, target: 12500, collect: [{ c: 5, n: 22 }, { c: 1, n: 22 }], blurb: 'The Aberdares' },
    { n: 12, moves: 15, target: 14000, collect: [{ c: 4, n: 25 }],                  blurb: 'Mount Kenya' },
    { n: 13, moves: 15, target: 16000, collect: [{ c: 0, n: 24 }, { c: 2, n: 24 }], blurb: 'Maasai Mara' },
    { n: 14, moves: 14, target: 18000, collect: [{ c: 5, n: 26 }],                  blurb: 'Meru' },
    { n: 15, moves: 14, target: 21000, collect: [{ c: 1, n: 26 }, { c: 0, n: 26 }], blurb: 'The Great Rift Valley' },
  ];

  /* Head-to-head: identical board from a shared seed, fixed moves, pure score. */
  const DUEL_MOVES = 20;
  const DUEL_LEVEL = { n: 0, moves: DUEL_MOVES, target: 999999999, collect: [], blurb: 'Duel' };

  const Match3 = {
    ROWS, COLS, COLORS, SPECIAL, LEVELS, BASE_POINTS, DUEL_LEVEL, DUEL_MOVES,
    mulberry32, idx, rowOf, colOf, cloneBoard,
    findRuns, findGroups, hasMatch, specialFor, expandClears, collapse,
    fillBoard, hasMove, newBoard,
    newGame, resolveMove, useBooster, goalsMet, starsFor, adjacent,
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = Match3;
  else global.Match3 = Match3;
})(typeof window !== 'undefined' ? window : globalThis);
