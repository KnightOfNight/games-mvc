const COLS = 'ABCDEFGHIJ'.split('');

let ws;
let playerNum = window.SHYSHIP_PLAYER_NUM;
let gameId = window.SHYSHIP_GAME_ID;
let currentTurn = 1;
let gameStatus = 'waiting';
let totalMoves = 0;
let myFires = new Set();
let shipNameCounts = {};
let autoPlay = false;
let targeting = null; // null = hunt mode; object = targeting a ship
let visibleBoard = 'enemy'; // 'enemy' | 'own' — mobile only

const statusBar       = document.getElementById('status-bar');
const ownGrid         = document.getElementById('own-grid');
const enemyGrid       = document.getElementById('enemy-grid');
const enemyPanel      = document.getElementById('enemy-panel');
const ownPanel        = document.getElementById('own-panel');
const boardTitleEnemy = document.getElementById('board-title-enemy');
const boardTitleOwn   = document.getElementById('board-title-own');
const fireNotifyModal = document.getElementById('fire-notify-modal');
const fireNotifyTitle = document.getElementById('fire-notify-title');
const fireNotifyText  = document.getElementById('fire-notify-text');
const fireNotifyOk    = document.getElementById('fire-notify-ok');
const waitingOverlay  = document.getElementById('waiting-overlay');
const resultOverlay   = document.getElementById('result-overlay');
const resultTitle     = document.getElementById('result-title');
const resultText      = document.getElementById('result-text');
const confirmModal    = document.getElementById('confirm-modal');
const confirmTitle    = document.getElementById('confirm-modal-title');
const confirmText     = document.getElementById('confirm-modal-text');
const confirmYes      = document.getElementById('confirm-yes');
const confirmNo       = document.getElementById('confirm-no');
const cancelOverlayBtn = document.getElementById('cancel-overlay-btn');
const cancelBtn       = document.getElementById('cancel-btn');
const forfeitBtn      = document.getElementById('forfeit-btn');
const cancelForm      = document.getElementById('cancel-form');
const forfeitForm     = document.getElementById('forfeit-form');

// ── Board visibility (mobile) ─────────────────────────────────────────────────

function isMobile() {
  return window.matchMedia('(max-width: 700px)').matches;
}

function updateBoardDisplay() {
  if (!isMobile()) {
    enemyPanel.classList.remove('is-hidden');
    ownPanel.classList.remove('is-hidden');
    boardTitleEnemy.classList.remove('is-link');
    boardTitleOwn.classList.remove('is-link');
    return;
  }
  if (visibleBoard === 'enemy') {
    enemyPanel.classList.remove('is-hidden');
    ownPanel.classList.add('is-hidden');
    boardTitleEnemy.classList.remove('is-link');
    boardTitleOwn.classList.add('is-link');
  } else {
    enemyPanel.classList.add('is-hidden');
    ownPanel.classList.remove('is-hidden');
    boardTitleEnemy.classList.add('is-link');
    boardTitleOwn.classList.remove('is-link');
  }
}

function setVisibleBoard(board) {
  visibleBoard = board;
  updateBoardDisplay();
}

boardTitleEnemy.addEventListener('click', () => { if (isMobile()) setVisibleBoard('enemy'); });
boardTitleOwn.addEventListener('click',   () => { if (isMobile()) setVisibleBoard('own'); });
window.addEventListener('resize', updateBoardDisplay);

// ── Auto-play ─────────────────────────────────────────────────────────────────

function inBounds(r, c) { return r >= 0 && r <= 9 && c >= 0 && c <= 9; }

function randomUnfired() {
  const candidates = [];
  for (let r = 0; r < 10; r++)
    for (let c = 0; c < 10; c++)
      if (!myFires.has(cellKey(r, c))) candidates.push([r, c]);
  return candidates.length ? candidates[Math.floor(Math.random() * candidates.length)] : null;
}

function reverseOrHunt() {
  if (!targeting.reversed) {
    targeting.dir = [-targeting.dir[0], -targeting.dir[1]];
    targeting.lastHit = targeting.firstHit;
    targeting.reversed = true;
    const nr = targeting.lastHit[0] + targeting.dir[0];
    const nc = targeting.lastHit[1] + targeting.dir[1];
    if (inBounds(nr, nc) && !myFires.has(cellKey(nr, nc))) return [nr, nc];
  }
  targeting = null;
  return randomUnfired();
}

function nextAutoCell() {
  if (targeting === null) return randomUnfired();

  if (targeting.dir !== null) {
    const nr = targeting.lastHit[0] + targeting.dir[0];
    const nc = targeting.lastHit[1] + targeting.dir[1];
    if (inBounds(nr, nc) && !myFires.has(cellKey(nr, nc))) return [nr, nc];
    return reverseOrHunt();
  }

  while (targeting.pending.length) {
    const [pr, pc] = targeting.pending[0];
    if (inBounds(pr, pc) && !myFires.has(cellKey(pr, pc))) return [pr, pc];
    targeting.pending.shift();
  }
  targeting = null;
  return randomUnfired();
}

function updateTargeting(row, col, isHit, sunk) {
  if (sunk)   { targeting = null; return; }
  if (!isHit) return;
  if (targeting === null) {
    targeting = {
      firstHit: [row, col], lastHit: [row, col],
      dir: null, reversed: false,
      pending: [[row-1,col],[row+1,col],[row,col-1],[row,col+1]],
    };
  } else if (targeting.dir === null) {
    targeting.dir = [row - targeting.firstHit[0], col - targeting.firstHit[1]];
    targeting.lastHit = [row, col];
  } else {
    targeting.lastHit = [row, col];
  }
}

function autoFire() {
  if (!autoPlay || gameStatus !== 'active' || currentTurn !== playerNum) return;
  const cell = nextAutoCell();
  if (!cell) return;
  ws.send(JSON.stringify({ type: 'fire', row: cell[0], col: cell[1] }));
}

// ── Enemy fire notification ───────────────────────────────────────────────────

function showFireNotify(isHit, shipName, sunk, onClose, isMine) {
  if (autoPlay) return;
  fireNotifyTitle.textContent = isHit ? 'HIT! HIT! HIT!' : 'MISS';
  if (isHit && shipName && !isMine) {
    const article = shipNameCounts[shipName] > 1 ? 'a' : 'the';
    fireNotifyText.textContent = sunk
      ? `Enemy sank ${article} ${shipName}!`
      : `Enemy hit ${article} ${shipName}!`;
  } else {
    fireNotifyText.textContent = '';
  }
  fireNotifyModal.classList.toggle('is-hit', isHit);

  let timer;

  function dismiss() {
    clearTimeout(timer);
    fireNotifyModal.classList.remove('is-open');
    fireNotifyModal.setAttribute('aria-hidden', 'true');
    fireNotifyOk.removeEventListener('click', dismiss);
    fireNotifyModal.querySelector('.modal-backdrop').removeEventListener('click', dismiss);
    if (onClose) onClose();
  }

  fireNotifyOk.addEventListener('click', dismiss);
  fireNotifyModal.querySelector('.modal-backdrop').addEventListener('click', dismiss);
  fireNotifyModal.classList.add('is-open');
  fireNotifyModal.setAttribute('aria-hidden', 'false');
  timer = setTimeout(dismiss, autoPlay ? 600 : 3000);
}

// ── Confirmation modal ────────────────────────────────────────────────────────

let confirmAction = null;

function showConfirm(title, text, onConfirm) {
  confirmTitle.textContent = title;
  confirmText.textContent  = text;
  confirmAction = onConfirm;
  confirmModal.classList.add('is-open');
  confirmModal.setAttribute('aria-hidden', 'false');
}

function hideConfirm() {
  confirmModal.classList.remove('is-open');
  confirmModal.setAttribute('aria-hidden', 'true');
  confirmAction = null;
}

confirmYes.addEventListener('click', () => { if (confirmAction) confirmAction(); hideConfirm(); });
confirmNo.addEventListener('click', hideConfirm);
confirmModal.querySelector('.modal-backdrop').addEventListener('click', hideConfirm);

cancelOverlayBtn.addEventListener('click', () =>
  showConfirm('Cancel Game', 'This will cancel the game for all players.', () => cancelForm.submit())
);
cancelBtn.addEventListener('click', () =>
  showConfirm('Cancel Game', 'This will cancel the game for all players.', () => cancelForm.submit())
);
forfeitBtn.addEventListener('click', () =>
  showConfirm('Forfeit Game', 'Are you sure? Your opponent will win.', () => forfeitForm.submit())
);

// ── Result overlay ────────────────────────────────────────────────────────────

function showResult(title, text, timeoutMs) {
  resultTitle.textContent = title;
  resultText.textContent  = text;
  resultOverlay.classList.add('is-open');
  resultOverlay.setAttribute('aria-hidden', 'false');
  waitingOverlay.classList.remove('is-open');
  waitingOverlay.setAttribute('aria-hidden', 'true');
  cancelBtn.hidden  = true;
  forfeitBtn.hidden = true;
  if (timeoutMs) setTimeout(() => { window.location.href = window.SHYSHIP_LOBBY_URL; }, timeoutMs);
}

// ── Action button visibility ──────────────────────────────────────────────────

function updateActionButtons() {
  if (gameStatus === 'waiting') {
    // Cancel is in the waiting overlay; nothing in the topbar
    cancelBtn.hidden  = true;
    forfeitBtn.hidden = true;
    return;
  }
  const canCancel = playerNum === 1 && totalMoves === 0;
  cancelBtn.hidden  = !canCancel;
  forfeitBtn.hidden = canCancel;
}

// ── Grid ──────────────────────────────────────────────────────────────────────

function cellKey(row, col) {
  return `${row},${col}`;
}

function buildGrid(container) {
  const corner = document.createElement('div');
  corner.className = 'grid-corner';
  container.appendChild(corner);

  for (const letter of COLS) {
    const el = document.createElement('div');
    el.className = 'grid-col-label';
    el.textContent = letter;
    container.appendChild(el);
  }

  for (let r = 0; r < 10; r++) {
    const rowLabel = document.createElement('div');
    rowLabel.className = 'grid-row-label';
    rowLabel.textContent = r + 1;
    container.appendChild(rowLabel);

    for (let c = 0; c < 10; c++) {
      const cell = document.createElement('div');
      cell.className = 'sea-cell';
      cell.dataset.row = r;
      cell.dataset.col = c;
      container.appendChild(cell);
    }
  }
}

function getCell(grid, row, col) {
  return grid.querySelector(`.sea-cell[data-row="${row}"][data-col="${col}"]`);
}

// ── Status bar ────────────────────────────────────────────────────────────────

function updateStatusBar() {
  statusBar.className = 'status-bar';
  if (gameStatus === 'waiting') {
    statusBar.textContent = 'Waiting for opponent…';
    return;
  }
  if (currentTurn === playerNum) {
    statusBar.textContent = 'Your turn — fire!';
    statusBar.classList.add('your-turn');
    enemyPanel.classList.add('my-turn');
  } else {
    statusBar.textContent = "Enemy's turn…";
    statusBar.classList.add('enemy-turn');
    enemyPanel.classList.remove('my-turn');
  }
}

// ── Board rendering ───────────────────────────────────────────────────────────

function renderMove(moverNum, row, col, isHit) {
  const grid = moverNum === playerNum ? enemyGrid : ownGrid;
  const cell = getCell(grid, row, col);
  if (cell) {
    cell.classList.add(isHit ? 'hit' : 'miss', 'pop');
    cell.addEventListener('animationend', () => cell.classList.remove('pop'), { once: true });
  }
}

// ── Message handlers ──────────────────────────────────────────────────────────

function applyState(msg) {
  playerNum    = msg.player_num;
  currentTurn  = msg.current_turn;
  gameStatus   = msg.status;
  totalMoves   = msg.moves.length;

  for (const ship of msg.ships_own) {
    shipNameCounts[ship.name] = (shipNameCounts[ship.name] || 0) + 1;
    for (const [r, c] of ship.cells) {
      const cell = getCell(ownGrid, r, c);
      if (cell) cell.classList.add('ship');
    }
  }

  for (const move of msg.moves) {
    renderMove(move.player_num, move.row, move.col, move.is_hit);
    if (move.player_num === playerNum) {
      myFires.add(cellKey(move.row, move.col));
    }
  }

  if (gameStatus === 'cancelled') {
    showResult('Game Cancelled', 'This game was cancelled by the creator.', 5000);
    return;
  }
  if (gameStatus === 'done') {
    if (msg.winner === playerNum) {
      showResult('You Win!', 'You sank all enemy ships!');
    } else if (msg.winner != null) {
      showResult('You Lose!', 'All your ships were sunk.');
    } else {
      showResult('Game Over', 'This game has ended.');
    }
    return;
  }

  if (gameStatus !== 'waiting') {
    waitingOverlay.classList.remove('is-open');
    waitingOverlay.setAttribute('aria-hidden', 'true');
  }

  if (gameStatus === 'active') {
    setVisibleBoard(currentTurn === playerNum ? 'enemy' : 'own');
  }

  updateActionButtons();
  updateStatusBar();
}

function applyMove(msg) {
  currentTurn = msg.next_turn;
  totalMoves++;
  renderMove(msg.player_num, msg.row, msg.col, msg.is_hit);
  if (msg.player_num === playerNum) {
    myFires.add(cellKey(msg.row, msg.col));
  }
  updateActionButtons();
  updateStatusBar();
  if (msg.player_num !== playerNum) {
    showFireNotify(msg.is_hit, msg.ship_name, msg.sunk, () => setVisibleBoard('enemy'));
  } else {
    showFireNotify(msg.is_hit, msg.ship_name, msg.sunk, () => setVisibleBoard('own'), true);
  }
  if (autoPlay && msg.player_num === playerNum) updateTargeting(msg.row, msg.col, msg.is_hit, msg.sunk);
  if (autoPlay) setTimeout(autoFire, 100);
}

function applyPlayerJoined(msg) {
  gameStatus = 'active';
  waitingOverlay.classList.remove('is-open');
  waitingOverlay.setAttribute('aria-hidden', 'true');
  setVisibleBoard(currentTurn === playerNum ? 'enemy' : 'own');
  updateActionButtons();
  updateStatusBar();
}

function applyError(msg) {
  const messages = {
    auth:       'Authentication error — please log in again.',
    not_found:  'Game not found.',
    not_player: 'You are not a player in this game.',
  };
  statusBar.textContent = messages[msg.code] || 'Connection error.';
  statusBar.className = 'status-bar enemy-turn';
}

function handleMessage(msg) {
  switch (msg.type) {
    case 'state':          applyState(msg); break;
    case 'move':           applyMove(msg); break;
    case 'player_joined':  applyPlayerJoined(msg); break;
    case 'error':          applyError(msg); break;
    case 'game_over':
      gameStatus = 'done';
      showResult(
        msg.winner === playerNum ? 'You Win!' : 'You Lose!',
        msg.winner === playerNum ? 'You sank all enemy ships!' : 'All your ships were sunk.'
      );
      break;
    case 'game_cancelled':
      showResult('Game Cancelled', 'The creator cancelled this game.', 5000); break;
    case 'game_forfeited':
      showResult('Game Over', msg.by === playerNum ? 'You forfeited.' : 'Your opponent forfeited. You win!', 5000); break;
  }
}

// ── Firing ────────────────────────────────────────────────────────────────────

function handleEnemyClick(e) {
  const cell = e.target.closest('.sea-cell');
  if (!cell) return;
  if (gameStatus !== 'active') return;
  if (currentTurn !== playerNum) return;
  const row = parseInt(cell.dataset.row, 10);
  const col = parseInt(cell.dataset.col, 10);
  if (myFires.has(cellKey(row, col))) return;
  ws.send(JSON.stringify({ type: 'fire', row, col }));
}

// ── Init ──────────────────────────────────────────────────────────────────────

function init() {
  buildGrid(ownGrid);
  buildGrid(enemyGrid);
  enemyGrid.addEventListener('click', handleEnemyClick);

  document.getElementById('auto-btn').addEventListener('click', () => {
    autoPlay = !autoPlay;
    document.getElementById('auto-btn').classList.toggle('is-active', autoPlay);
    if (autoPlay) { setVisibleBoard('own'); setTimeout(autoFire, 400); }
  });

  const wsProto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${wsProto}//${location.host}/ws/shyship/${gameId}/`);

  ws.onmessage = (e) => handleMessage(JSON.parse(e.data));
  ws.onclose = () => {
    statusBar.innerHTML = 'Disconnected — <a href="" onclick="location.reload();return false;" style="color:inherit;text-decoration:underline;">refresh</a> to reconnect.';
    statusBar.className = 'status-bar enemy-turn';
  };
}

init();
