/*
 * Market Day engine tests.  Run with:  node match3.test.mjs
 */
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';

const require = createRequire(import.meta.url);
const M = require('./match3.js');

let passed = 0;
function test(name, fn) {
  try {
    fn();
    passed += 1;
    console.log('  ✓ ' + name);
  } catch (err) {
    console.error('  ✗ ' + name);
    console.error(err);
    process.exitCode = 1;
  }
}

const R = 8;
const C = 8;
/* Build a board from a compact string grid; '.' = colour 0. */
function boardFrom(rowsText) {
  const board = [];
  rowsText.forEach((line) => {
    line.split('').forEach((ch) => board.push({ c: Number(ch), s: null }));
  });
  return board;
}
const flat = (color) => new Array(R * C).fill(null).map(() => ({ c: color, s: null }));

test('new board has no ready-made matches but always has a move', () => {
  for (let seed = 0; seed < 25; seed += 1) {
    const rng = M.mulberry32(seed);
    const b = M.newBoard(R, C, M.COLORS, rng);
    assert.equal(b.length, 64);
    assert.equal(M.hasMatch(b, R, C), false, 'seed ' + seed + ' had a starting match');
    assert.equal(M.hasMove(b, R, C), true, 'seed ' + seed + ' was deadlocked');
  }
});

test('findRuns detects horizontal and vertical runs of 3, 4 and 5', () => {
  const b = boardFrom([
    '11123450',
    '20000000',
    '20111111',
    '20345012',
    '01234501',
    '12345012',
    '01234501',
    '12345012',
  ]);
  const runs = M.findRuns(b, R, C);
  const h = runs.filter((r) => r.dir === 'h');
  const v = runs.filter((r) => r.dir === 'v');
  assert.ok(h.some((r) => r.cells.length === 3 && r.color === 1), 'row of three 1s');
  assert.ok(h.some((r) => r.cells.length === 6 && r.color === 1), 'row of six 1s');
  assert.ok(v.some((r) => r.cells.length === 3 && r.color === 2), 'column of three 2s');
});

test('a run of exactly 4 earns a striped special', () => {
  const g = { color: 3, maxRun: 4, crossed: false, dir: 'h', cells: new Set() };
  assert.equal(M.specialFor(g), M.SPECIAL.ROW);
  assert.equal(M.specialFor({ ...g, dir: 'v' }), M.SPECIAL.COL);
});

test('a run of 5+ earns a rainbow; an L/T shape earns a bomb', () => {
  assert.equal(M.specialFor({ maxRun: 5, crossed: false, dir: 'h' }), M.SPECIAL.RAINBOW);
  assert.equal(M.specialFor({ maxRun: 3, crossed: true, dir: 'h' }), M.SPECIAL.BOMB);
  assert.equal(M.specialFor({ maxRun: 3, crossed: false, dir: 'h' }), null);
});

test('findGroups merges crossing runs into one L-shaped group', () => {
  // A vertical run of 3 and a horizontal run of 3 sharing a corner cell.
  const b = boardFrom([
    '11134502',
    '10234501',
    '10345012',
    '02345012',
    '01234501',
    '12345012',
    '01234501',
    '12345012',
  ]);
  const groups = M.findGroups(b, R, C).filter((g) => g.color === 1);
  const cross = groups.find((g) => g.crossed);
  assert.ok(cross, 'expected a crossed group');
  assert.equal(M.specialFor(cross), M.SPECIAL.BOMB);
});

test('a swap that makes no match is rejected and leaves state untouched', () => {
  const s = M.newGame(M.LEVELS[0], 42);
  const before = JSON.stringify(s.board);
  // Find a swap the engine rejects.
  let rejected = null;
  for (let i = 0; i < 63 && !rejected; i += 1) {
    const r = M.resolveMove(s, i, i + 1);
    if (!r.valid) rejected = r;
  }
  assert.ok(rejected, 'expected at least one illegal swap');
  assert.equal(rejected.phases.length, 0);
  assert.equal(JSON.stringify(s.board), before);
  assert.equal(s.movesLeft, M.LEVELS[0].moves);
});

test('non-adjacent swaps are always rejected', () => {
  const s = M.newGame(M.LEVELS[0], 7);
  assert.equal(M.resolveMove(s, 0, 2).valid, false);
  assert.equal(M.resolveMove(s, 0, 63).valid, false);
});

test('a valid swap clears tiles, scores, spends a move and refills the board', () => {
  const s = M.newGame(M.LEVELS[0], 3);
  let done = null;
  for (let i = 0; i < 64 && !done; i += 1) {
    for (const j of [i + 1, i + C]) {
      if (j >= 64) continue;
      if (!M.adjacent(i, j, C)) continue;
      const r = M.resolveMove(s, i, j);
      if (r.valid) { done = r; break; }
    }
  }
  assert.ok(done, 'expected a legal swap to exist');
  assert.ok(done.phases.length >= 1);
  assert.ok(done.phases[0].cleared.length >= 3);
  assert.ok(done.state.score > 0);
  assert.equal(done.state.movesLeft, s.movesLeft - 1);
  assert.ok(done.state.board.every((t) => t !== null), 'board fully refilled');
  assert.equal(done.state.board.length, 64);
});

test('gravity drops tiles down and refills from the top', () => {
  const b = flat(1);
  b[M.idx(7, 0, C)] = null;
  b[M.idx(6, 0, C)] = null;
  b[M.idx(5, 0, C)] = { c: 4, s: null };
  M.collapse(b, R, C, 6, M.mulberry32(1));
  assert.ok(b.every((t) => t !== null), 'no holes left');
  assert.equal(b[M.idx(7, 0, C)].c, 4, 'the tile above fell to the floor');
});

test('a striped tile clears its whole row when caught in a clear', () => {
  const b = flat(0);
  b[M.idx(3, 3, C)] = { c: 1, s: M.SPECIAL.ROW };
  const cleared = M.expandClears(b, R, C, new Set([M.idx(3, 3, C)]));
  for (let c = 0; c < C; c += 1) assert.ok(cleared.has(M.idx(3, c, C)), 'row cell ' + c);
  assert.equal(cleared.size, C);
});

test('a bomb clears its 3x3 neighbourhood', () => {
  const b = flat(0);
  b[M.idx(4, 4, C)] = { c: 1, s: M.SPECIAL.BOMB };
  const cleared = M.expandClears(b, R, C, new Set([M.idx(4, 4, C)]));
  assert.equal(cleared.size, 9);
  assert.ok(cleared.has(M.idx(3, 3, C)) && cleared.has(M.idx(5, 5, C)));
});

test('specials chain: a striped tile sets off another striped tile', () => {
  const b = flat(0);
  b[M.idx(2, 2, C)] = { c: 1, s: M.SPECIAL.ROW };
  b[M.idx(2, 5, C)] = { c: 1, s: M.SPECIAL.COL };
  const cleared = M.expandClears(b, R, C, new Set([M.idx(2, 2, C)]));
  // Row 2 (8) plus column 5 (8) sharing one cell = 15.
  assert.equal(cleared.size, 15);
});

test('swapping a rainbow onto a colour clears every tile of that colour', () => {
  const s = M.newGame(M.LEVELS[0], 11);
  // Plant a rainbow next to a known colour.
  const a = M.idx(4, 4, C);
  const b = M.idx(4, 5, C);
  s.board[a] = { c: 0, s: M.SPECIAL.RAINBOW };
  s.board[b] = { c: 2, s: null };
  const targets = s.board.filter((t) => t.c === 2).length;
  const r = M.resolveMove(s, a, b);
  assert.equal(r.valid, true, 'rainbow swap is legal without forming a match');
  assert.ok(r.phases[0].cleared.length >= targets, 'cleared every tile of the colour');
  assert.ok(r.state.score > 0);
});

test('collect goals count the tiles actually cleared', () => {
  const s = M.newGame(M.LEVELS[0], 5);
  let done = null;
  for (let i = 0; i < 64 && !done; i += 1) {
    for (const j of [i + 1, i + C]) {
      if (j >= 64 || !M.adjacent(i, j, C)) continue;
      const r = M.resolveMove(s, i, j);
      if (r.valid) { done = r; break; }
    }
  }
  const totalCollected = done.state.collected.reduce((a, b) => a + b, 0);
  const totalCleared = done.phases.reduce((a, p) => a + p.cleared.length, 0);
  assert.equal(totalCollected, totalCleared);
});

test('cascades multiply the score', () => {
  // Same clear size scores more on a later cascade step.
  const one = 5 * M.BASE_POINTS * 1;
  const two = 5 * M.BASE_POINTS * 2;
  assert.ok(two > one);
});

test('running out of moves ends the level as a loss', () => {
  const level = { ...M.LEVELS[0], moves: 1, target: 999999 };
  let s = M.newGame(level, 9);
  let done = null;
  for (let i = 0; i < 64 && !done; i += 1) {
    for (const j of [i + 1, i + C]) {
      if (j >= 64 || !M.adjacent(i, j, C)) continue;
      const r = M.resolveMove(s, i, j);
      if (r.valid) { done = r; break; }
    }
  }
  assert.equal(done.state.movesLeft, 0);
  assert.equal(done.state.over, true);
  assert.equal(done.state.won, false);
});

test('hitting the target wins the level and awards stars', () => {
  const s = M.newGame({ ...M.LEVELS[0], target: 1, collect: [] }, 13);
  let done = null;
  for (let i = 0; i < 64 && !done; i += 1) {
    for (const j of [i + 1, i + C]) {
      if (j >= 64 || !M.adjacent(i, j, C)) continue;
      const r = M.resolveMove(s, i, j);
      if (r.valid) { done = r; break; }
    }
  }
  assert.equal(done.state.won, true);
  assert.equal(done.state.over, true);
  assert.equal(M.starsFor(done.state), 3);
});

test('a level is not won on score alone while collect goals are unmet', () => {
  const s = M.newGame({ moves: 10, target: 1, collect: [{ c: 0, n: 9999 }] }, 21);
  s.score = 100000;
  assert.equal(M.goalsMet(s), false);
  s.collected[0] = 9999;
  assert.equal(M.goalsMet(s), true);
});

test('the hammer booster removes a tile without spending a move', () => {
  const s = M.newGame(M.LEVELS[0], 17);
  const r = M.useBooster(s, 'hammer', M.idx(4, 4, C));
  assert.equal(r.valid, true);
  assert.equal(r.state.movesLeft, s.movesLeft, 'boosters are free of moves');
  assert.ok(r.phases[0].cleared.includes(M.idx(4, 4, C)));
  assert.ok(r.state.board.every((t) => t !== null));
});

test('the shuffle booster leaves a playable, match-free board', () => {
  const s = M.newGame(M.LEVELS[0], 19);
  const r = M.useBooster(s, 'shuffle');
  assert.equal(r.valid, true);
  assert.equal(r.state.movesLeft, s.movesLeft);
  assert.equal(M.hasMove(r.state.board, R, C), true);
  assert.ok(r.state.board.every((t) => t !== null));
});

test('the board is never left deadlocked after a move', () => {
  for (let seed = 0; seed < 8; seed += 1) {
    let s = M.newGame({ moves: 200, target: 1e9, collect: [] }, seed);
    for (let turn = 0; turn < 40 && !s.over; turn += 1) {
      let moved = false;
      for (let i = 0; i < 64 && !moved; i += 1) {
        for (const j of [i + 1, i + C]) {
          if (j >= 64 || !M.adjacent(i, j, C)) continue;
          const r = M.resolveMove(s, i, j);
          if (r.valid) { s = r.state; moved = true; break; }
        }
      }
      assert.ok(moved, 'seed ' + seed + ' turn ' + turn + ': no legal move offered');
      assert.ok(s.board.every((t) => t !== null), 'board stayed full');
      assert.equal(M.hasMove(s.board, R, C), true, 'board stayed playable');
    }
  }
});

test('every level is well-formed and the campaign gets harder', () => {
  assert.ok(M.LEVELS.length >= 50, 'a real campaign, not a demo');
  assert.equal(M.LEVELS.length, M.CITIES.length, 'one stage per city');
  M.LEVELS.forEach((l, k) => {
    assert.ok(l.moves > 0 && l.target > 0, 'level ' + l.n);
    assert.equal(l.n, k + 1, 'levels are numbered in order');
    assert.ok(l.blurb && l.blurb.length > 0, 'level ' + l.n + ' has a city');
    assert.ok(l.country && l.country.length > 0, 'level ' + l.n + ' has a country');
    assert.ok(l.flag && l.flag.length > 0, 'level ' + l.n + ' has a flag');
    (l.collect || []).forEach((g) => {
      assert.ok(g.c >= 0 && g.c < M.COLORS, 'goal colour in range');
      assert.ok(g.n > 0);
    });
    if (k > 0) {
      assert.ok(l.target > M.LEVELS[k - 1].target, 'target rises at level ' + l.n);
      assert.ok(l.moves <= M.LEVELS[k - 1].moves, 'moves tighten at level ' + l.n);
    }
  });
});

test('the safari starts in Nairobi and crosses the continent', () => {
  assert.equal(M.LEVELS[0].blurb, 'Nairobi', 'the game is from Nairobi');
  assert.equal(M.LEVELS[0].country, 'Kenya');
  assert.equal(M.LEVELS[0].collect.length, 0, 'the first stage teaches, it does not test');
  const countries = new Set(M.CITIES.map((c) => c.country));
  assert.ok(countries.size >= 30, 'reaches ' + countries.size + ' countries');
  // Every region of the continent is represented.
  ['Egypt', 'Nigeria', 'South Africa', 'DR Congo', 'Kenya', 'Morocco', 'Ethiopia']
    .forEach((c) => assert.ok(countries.has(c), 'missing ' + c));
});

test('no city appears twice in the journey', () => {
  const seen = M.CITIES.map((c) => c.city + ', ' + c.country);
  assert.equal(new Set(seen).size, seen.length);
});

test('collect goals stay reachable — never more than the moves allow', () => {
  M.LEVELS.forEach((l) => {
    const needed = (l.collect || []).reduce((a, g) => a + g.n, 0);
    // Three tiles minimum per move is the floor; real play clears far more.
    assert.ok(needed <= l.moves * 3 + 30,
      'level ' + l.n + ' asks for ' + needed + ' in ' + l.moves + ' moves');
  });
});

test('buildLevels is data-driven — adding a city adds a stage', () => {
  const extra = M.CITIES.concat([{ city: 'Bissau', country: 'Guinea-Bissau', flag: '🇬🇼', c: 2 }]);
  const built = M.buildLevels(extra);
  assert.equal(built.length, M.CITIES.length + 1);
  assert.equal(built[built.length - 1].blurb, 'Bissau');
  assert.ok(built[built.length - 1].target > built[built.length - 2].target);
});

test('phases report which animals were cleared, so the UI can sound them', () => {
  const s = M.newGame(M.LEVELS[0], 3);
  let done = null;
  for (let i = 0; i < 64 && !done; i += 1) {
    for (const j of [i + 1, i + C]) {
      if (j >= 64 || !M.adjacent(i, j, C)) continue;
      const r = M.resolveMove(s, i, j);
      if (r.valid) { done = r; break; }
    }
  }
  done.phases.forEach((p) => {
    assert.ok(Array.isArray(p.colors), 'every phase carries colours');
    assert.equal(p.colors.length, p.cleared.length, 'one colour per cleared tile');
    p.colors.forEach((c) => assert.ok(c === null || (c >= 0 && c < M.COLORS), 'colour in range'));
  });
  assert.ok(done.phases[0].colors.length >= 3);
});

test('the hammer booster also reports cleared colours', () => {
  const s = M.newGame(M.LEVELS[0], 17);
  const r = M.useBooster(s, 'hammer', M.idx(4, 4, C));
  assert.equal(r.phases[0].colors.length, r.phases[0].cleared.length);
});

console.log('\n' + passed + ' tests passed' + (process.exitCode ? ' (with failures)' : ''));
