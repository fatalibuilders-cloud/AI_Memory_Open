/*
 * Oware Legends — game engine (Abapa rules)
 *
 * Pure, dependency-free rules logic shared by the browser UI (index.html)
 * and the Node test suite (engine.test.mjs).
 *
 * Board layout: 12 pits, indices 0-11.
 *   Player 0 (South / human by default) owns pits 0-5.
 *   Player 1 (North / AI by default)   owns pits 6-11.
 * Sowing is counter-clockwise: 0 → 1 → … → 11 → 0.
 *
 * Rules implemented (Abapa / tournament variant):
 *   - 4 seeds per pit at start (48 total).
 *   - The origin pit is always skipped when sowing (matters with 12+ seeds).
 *   - Capture: last seed lands in an opponent pit leaving 2 or 3 seeds →
 *     capture it plus any unbroken backwards chain of opponent pits with 2-3.
 *   - Grand slam: a move that would capture ALL opponent seeds is legal but
 *     forfeits its captures.
 *   - Feeding: if the opponent has no seeds, you must play a move that gives
 *     them seeds when one exists; if none exists, you collect your own
 *     remaining seeds and the game ends.
 *   - A player reaching 25+ captured seeds wins. If the game stalls
 *     (MOVE_CAP moves), each player collects the seeds on their own side.
 */
(function (global) {
  'use strict';

  const TOTAL_SEEDS = 48;
  const WIN_THRESHOLD = 25;
  const MOVE_CAP = 250;

  function newGame(firstPlayer = 0) {
    return {
      board: new Array(12).fill(4),
      captured: [0, 0],
      turn: firstPlayer,
      moves: 0,
      ended: false,
      // 'win25' | 'starved' | 'stalled' | null
      endReason: null,
    };
  }

  function cloneState(s) {
    return {
      board: s.board.slice(),
      captured: s.captured.slice(),
      turn: s.turn,
      moves: s.moves,
      ended: s.ended,
      endReason: s.endReason,
    };
  }

  function ownPits(player) {
    return player === 0 ? [0, 1, 2, 3, 4, 5] : [6, 7, 8, 9, 10, 11];
  }

  function isOwnPit(player, pit) {
    return player === 0 ? pit <= 5 : pit >= 6;
  }

  function rowSum(board, player) {
    let sum = 0;
    for (const p of ownPits(player)) sum += board[p];
    return sum;
  }

  /* Does sowing from `pit` drop at least one seed in the opponent's row? */
  function movefeeds(state, pit) {
    const rowEnd = state.turn === 0 ? 5 : 11;
    return state.board[pit] > rowEnd - pit;
  }

  function legalMoves(state) {
    if (state.ended) return [];
    const mine = ownPits(state.turn).filter((p) => state.board[p] > 0);
    if (rowSum(state.board, 1 - state.turn) === 0) {
      const feeding = mine.filter((p) => movefeeds(state, p));
      if (feeding.length > 0) return feeding;
      // Cannot feed: no legal moves — caller ends the game via applyStarvation.
      return [];
    }
    return mine;
  }

  /* Sow seeds from `pit` on a board copy. Returns { board, lastPit, path }. */
  function sow(board, pit) {
    const b = board.slice();
    let seeds = b[pit];
    b[pit] = 0;
    let i = pit;
    const path = [];
    while (seeds > 0) {
      i = (i + 1) % 12;
      if (i === pit) continue; // origin pit is always skipped
      b[i] += 1;
      path.push(i);
      seeds -= 1;
    }
    return { board: b, lastPit: path[path.length - 1], path };
  }

  /*
   * Apply a move. Returns a NEW state plus animation metadata:
   *   { state, path, capturedPits, capturedCount, grandSlam }
   * Throws on illegal moves.
   */
  function applyMove(state, pit) {
    const legal = legalMoves(state);
    if (!legal.includes(pit)) {
      throw new Error('Illegal move: pit ' + pit + ' (turn ' + state.turn + ')');
    }
    const s = cloneState(state);
    const { board, lastPit, path } = sow(s.board, pit);
    s.board = board;

    // Determine captures: backwards chain of opponent pits holding 2 or 3.
    const opponent = 1 - s.turn;
    const capturedPits = [];
    let grandSlam = false;
    if (isOwnPit(opponent, lastPit) && (board[lastPit] === 2 || board[lastPit] === 3)) {
      let i = lastPit;
      while (isOwnPit(opponent, i) && (board[i] === 2 || board[i] === 3)) {
        capturedPits.push(i);
        i -= 1;
        if (i < 0) break;
      }
      const captureSum = capturedPits.reduce((acc, p) => acc + board[p], 0);
      if (captureSum === rowSum(board, opponent)) {
        // Grand slam: the move stands but captures are forfeited.
        grandSlam = true;
        capturedPits.length = 0;
      }
    }

    let capturedCount = 0;
    for (const p of capturedPits) {
      capturedCount += s.board[p];
      s.board[p] = 0;
    }
    s.captured[s.turn] += capturedCount;
    s.moves += 1;
    s.turn = opponent;

    // End-of-game checks.
    if (s.captured[0] >= WIN_THRESHOLD || s.captured[1] >= WIN_THRESHOLD) {
      s.ended = true;
      s.endReason = 'win25';
    } else if (s.moves >= MOVE_CAP) {
      // Stalemate guard: each player keeps the seeds on their own side.
      s.captured[0] += rowSum(s.board, 0);
      s.captured[1] += rowSum(s.board, 1);
      s.board.fill(0);
      s.ended = true;
      s.endReason = 'stalled';
    } else if (legalMoves(s).length === 0) {
      // Next player is starved and cannot be fed (or has nothing to play):
      // they collect nothing; the mover-side seeds go to whoever owns them.
      s.captured[0] += rowSum(s.board, 0);
      s.captured[1] += rowSum(s.board, 1);
      s.board.fill(0);
      s.ended = true;
      s.endReason = 'starved';
    }

    return { state: s, path, capturedPits, capturedCount, grandSlam };
  }

  /* -1 = draw, 0 or 1 = winning player. Only valid when state.ended. */
  function winner(state) {
    if (!state.ended) return null;
    if (state.captured[0] === state.captured[1]) return -1;
    return state.captured[0] > state.captured[1] ? 0 : 1;
  }

  /* ---------------- AI (minimax with alpha-beta) ---------------- */

  function evaluate(state, player) {
    const opp = 1 - player;
    let score = 6 * (state.captured[player] - state.captured[opp]);
    score += 0.5 * (rowSum(state.board, player) - rowSum(state.board, opp));
    // Penalise own pits sitting on 1 or 2 seeds (capturable next turn).
    for (const p of ownPits(player)) {
      if (state.board[p] === 1 || state.board[p] === 2) score -= 0.4;
    }
    for (const p of ownPits(opp)) {
      if (state.board[p] === 1 || state.board[p] === 2) score += 0.4;
    }
    return score;
  }

  function minimax(state, depth, alpha, beta, player) {
    if (state.ended) {
      const w = winner(state);
      if (w === player) return 1000 + state.captured[player];
      if (w === -1) return 0;
      return -1000 - state.captured[1 - player];
    }
    if (depth === 0) return evaluate(state, player);

    const moves = legalMoves(state);
    const maximizing = state.turn === player;
    let best = maximizing ? -Infinity : Infinity;
    for (const m of moves) {
      const { state: next } = applyMove(state, m);
      const val = minimax(next, depth - 1, alpha, beta, player);
      if (maximizing) {
        best = Math.max(best, val);
        alpha = Math.max(alpha, val);
      } else {
        best = Math.min(best, val);
        beta = Math.min(beta, val);
      }
      if (beta <= alpha) break;
    }
    return best;
  }

  /*
   * Pick a move for state.turn.
   * difficulty: 'easy' | 'medium' | 'hard'
   */
  function bestMove(state, difficulty = 'medium', rng = Math.random) {
    const moves = legalMoves(state);
    if (moves.length === 0) return null;
    if (moves.length === 1) return moves[0];

    const depth = difficulty === 'easy' ? 1 : difficulty === 'medium' ? 3 : 6;
    // Easy keeps a human feel: sometimes just play something plausible.
    if (difficulty === 'easy' && rng() < 0.35) {
      return moves[Math.floor(rng() * moves.length)];
    }

    let best = -Infinity;
    let choice = moves[0];
    for (const m of moves) {
      const { state: next } = applyMove(state, m);
      const val = minimax(next, depth - 1, -Infinity, Infinity, state.turn);
      if (val > best || (val === best && rng() < 0.5)) {
        best = val;
        choice = m;
      }
    }
    return choice;
  }

  const OwareEngine = {
    TOTAL_SEEDS,
    WIN_THRESHOLD,
    MOVE_CAP,
    newGame,
    cloneState,
    ownPits,
    isOwnPit,
    rowSum,
    legalMoves,
    sow,
    applyMove,
    winner,
    evaluate,
    bestMove,
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = OwareEngine;
  } else {
    global.OwareEngine = OwareEngine;
  }
})(typeof window !== 'undefined' ? window : globalThis);
