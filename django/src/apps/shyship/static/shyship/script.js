const COLS = 'ABCDEFGHIJ'.split('');

let ws;
let playerNum = window.SHYSHIP_PLAYER_NUM;
let gameId = window.SHYSHIP_GAME_ID;
let currentTurn = 1;
let gameStatus = 'waiting';
let totalMoves = 0;
let myFires = new Set();
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

// ── Enemy fire notification ───────────────────────────────────────────────────

function showFireNotify(isHit, onClose, isMine) {
  fireNotifyTitle.textContent = isHit ? 'HIT!' : 'MISS';
  if (isMine) {
    fireNotifyText.textContent = isHit ? 'You hit an enemy ship!' : 'Your shot missed.';
  } else {
    fireNotifyText.textContent = isHit ? 'Your ship was struck.' : 'The shot missed your waters.';
  }

  function dismiss() {
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

function showResult(title, text) {
  resultTitle.textContent = title;
  resultText.textContent  = text;
  resultOverlay.classList.add('is-open');
  resultOverlay.setAttribute('aria-hidden', 'false');
  waitingOverlay.classList.remove('is-open');
  waitingOverlay.setAttribute('aria-hidden', 'true');
  cancelBtn.hidden  = true;
  forfeitBtn.hidden = true;
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

  for (const [r, c] of msg.ships_own) {
    const cell = getCell(ownGrid, r, c);
    if (cell) cell.classList.add('ship');
  }

  for (const move of msg.moves) {
    renderMove(move.player_num, move.row, move.col, move.is_hit);
    if (move.player_num === playerNum) {
      myFires.add(cellKey(move.row, move.col));
    }
  }

  if (gameStatus === 'cancelled') {
    showResult('Game Cancelled', 'This game was cancelled by the creator.');
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
    showFireNotify(msg.is_hit, () => setVisibleBoard('enemy'));
  } else {
    showFireNotify(msg.is_hit, () => setVisibleBoard('own'), true);
  }
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
      showResult('Game Cancelled', 'The creator cancelled this game.'); break;
    case 'game_forfeited':
      showResult('Game Over', msg.by === playerNum ? 'You forfeited.' : 'Your opponent forfeited. You win!'); break;
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

  const wsProto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${wsProto}//${location.host}/ws/shyship/${gameId}/`);

  ws.onmessage = (e) => handleMessage(JSON.parse(e.data));
  ws.onclose = () => {
    statusBar.textContent = 'Disconnected — reload to reconnect.';
    statusBar.className = 'status-bar enemy-turn';
  };
}

init();
