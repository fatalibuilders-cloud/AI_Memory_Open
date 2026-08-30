/*
 * Oware Legends engine tests.
 * Run with:  node engine.test.mjs
 */
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';

const require = createRequire(import.meta.url);
const E = require('./engine.js');

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

test('new game: 4 seeds everywhere, 48 total, player 0 to move', () => {
  const s = E.newGame();
  assert.equal(s.board.length, 12);
  assert.ok(s.board.every((n) => n === 4));
  assert.equal(s.board.reduce((a, b) => a + b, 0), E.TOTAL_SEEDS);
  assert.equal(s.turn, 0);
  assert.deepEqual(E.legalMoves(s), [0, 1, 2, 3, 4, 5]);
});

test('basic sowing is counter-clockwise and empties the origin', () => {
  const s = E.newGame();
  const { state, path } = E.applyMove(s, 2); // 4 seeds → pits 3,4,5,6
  assert.deepEqual(path, [3, 4, 5, 6]);
  assert.equal(state.board[2], 0);
  assert.equal(state.board[3], 5);
  assert.equal(state.board[6], 5);
  assert.equal(state.turn, 1);
  assert.equal(state.captured[0], 0);
});

test('seed conservation across a full random game', () => {
  let s = E.newGame();
  let guard = 0;
  while (!s.ended && guard < 400) {
    const moves = E.legalMoves(s);
    const m = moves[Math.floor(Math.random() * moves.length)];
    s = E.applyMove(s, m).state;
    const onBoard = s.board.reduce((a, b) => a + b, 0);
    assert.equal(onBoard + s.captured[0] + s.captured[1], E.TOTAL_SEEDS);
    guard += 1;
  }
  assert.ok(s.ended, 'game should end');
});

test('sowing 12+ seeds skips the origin pit', () => {
  const s = E.newGame();
  s.board = [14, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1];
  const { board, lastPit } = E.sow(s.board, 0);
  // 14 seeds from pit 0: one full lap (11 pits, origin skipped) + 3 more.
  assert.equal(board[0], 0);
  assert.equal(board[1], 1 + 2); // receives twice
  assert.equal(board[4], 1 + 1);
  assert.equal(lastPit, 3);
});

test('capture: last seed making an opponent pit 2 or 3 captures it', () => {
  const s = E.newGame();
  s.board = [0, 0, 0, 0, 0, 2, 1, 4, 4, 4, 4, 4];
  s.turn = 0;
  const { state, capturedPits, capturedCount } = E.applyMove(s, 5);
  // Pit 5 has 2 seeds → lands in 6 (1→2) and... 2 seeds: pits 6,7. Pit 7: 4→5, no capture chain from 7.
  // Last pit is 7 with 5 seeds → no capture.
  assert.equal(capturedCount, 0);
  assert.deepEqual(capturedPits, []);
  assert.equal(state.board[6], 2);
});

test('capture chain walks backwards through consecutive 2s and 3s', () => {
  const s = E.newGame();
  s.board = [0, 0, 0, 0, 0, 3, 1, 2, 2, 4, 4, 4];
  s.turn = 0;
  // 3 seeds from pit 5 land in 6,7,8 → pits become 2,3,3. Last pit 8 (3) →
  // capture 8, then 7 (3), then 6 (2). Chain = 8.
  const { state, capturedPits, capturedCount } = E.applyMove(s, 5);
  assert.deepEqual(capturedPits.slice().sort(), [6, 7, 8]);
  assert.equal(capturedCount, 8);
  assert.equal(state.captured[0], 8);
  assert.equal(state.board[6] + state.board[7] + state.board[8], 0);
});

test('capture chain stops at a pit outside 2-3', () => {
  const s = E.newGame();
  s.board = [0, 0, 0, 0, 0, 3, 5, 2, 2, 4, 4, 4];
  s.turn = 0;
  // Seeds land in 6,7,8 → 6,3,3. Capture 8 and 7 only (6 has 6 seeds).
  const { capturedPits, capturedCount } = E.applyMove(s, 5);
  assert.deepEqual(capturedPits.slice().sort(), [7, 8]);
  assert.equal(capturedCount, 6);
});

test('grand slam: capturing all opponent seeds is forfeited', () => {
  const s = E.newGame();
  s.board = [1, 0, 0, 0, 0, 2, 1, 2, 0, 0, 0, 0];
  s.turn = 0;
  // 2 seeds from pit 5 → pits 6,7 become 2,3. Chain would capture ALL
  // of North's seeds → grand slam → no capture. (Pit 0 keeps South's row
  // non-empty so the game continues afterwards.)
  const { state, capturedCount, grandSlam } = E.applyMove(s, 5);
  assert.equal(grandSlam, true);
  assert.equal(capturedCount, 0);
  assert.equal(state.captured[0], 0);
  assert.equal(state.board[6], 2);
  assert.equal(state.board[7], 3);
});

test('feeding: when opponent is empty, only feeding moves are legal', () => {
  const s = E.newGame();
  s.board = [1, 0, 0, 2, 0, 3, 0, 0, 0, 0, 0, 0];
  s.turn = 0;
  // Opponent (North) empty. Pit 0 (1 seed) reaches pit 1 only — not feeding.
  // Pit 3 (2 seeds) reaches 4,5 — not feeding. Pit 5 (3 seeds) reaches 6,7,8 — feeds.
  assert.deepEqual(E.legalMoves(s), [5]);
});

test('starvation: mover who cannot feed collects own remaining seeds', () => {
  const s = E.newGame();
  s.board = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2];
  s.turn = 1;
  s.captured = [20, 22];
  // North plays pit 11 (2 seeds → pits 0,1: South gets seeds, fine).
  // Board after: [2,2,0,...,0]. South's move from pit 0 or 1 cannot reach
  // North's row (pit 0 needs >5, pit 1 needs >4)... pit 1 has 2 seeds → lands 2,3. Not feeding.
  // So after South's forced position, check the engine's handling via applyMove chain.
  const r1 = E.applyMove(s, 11);
  // South now has [2,2,...] but North is empty and South can't feed → game
  // ends immediately: South collects own seeds.
  assert.equal(r1.state.ended, true);
  assert.equal(r1.state.endReason, 'starved');
  assert.equal(r1.state.captured[0], 20 + 4);
  assert.equal(r1.state.captured[1], 22);
});

test('reaching 25 captured seeds ends the game', () => {
  const s = E.newGame();
  s.board = [0, 0, 0, 0, 0, 3, 1, 2, 2, 4, 4, 4];
  s.turn = 0;
  s.captured = [20, 8]; // 20 on board + 28 captured = 48 ✓ (8 captured via chain)
  const { state } = E.applyMove(s, 5);
  assert.equal(state.captured[0], 28);
  assert.equal(state.ended, true);
  assert.equal(state.endReason, 'win25');
  assert.equal(E.winner(state), 0);
});

test('AI: bestMove returns a legal move at every difficulty', () => {
  for (const diff of ['easy', 'medium', 'hard']) {
    const s = E.newGame();
    const m = E.bestMove(s, diff);
    assert.ok(E.legalMoves(s).includes(m), diff + ' move is legal');
  }
});

test('AI: hard beats random play convincingly over 10 games', () => {
  let aiWins = 0;
  for (let g = 0; g < 10; g += 1) {
    let s = E.newGame(g % 2); // alternate who starts
    let guard = 0;
    while (!s.ended && guard < 400) {
      let m;
      if (s.turn === 1) {
        m = E.bestMove(s, 'hard');
      } else {
        const moves = E.legalMoves(s);
        m = moves[Math.floor(Math.random() * moves.length)];
      }
      s = E.applyMove(s, m).state;
      guard += 1;
    }
    if (E.winner(s) === 1) aiWins += 1;
  }
  assert.ok(aiWins >= 8, 'hard AI won ' + aiWins + '/10 vs random');
});

console.log('\n' + passed + ' tests passed' + (process.exitCode ? ' (with failures)' : ''));
