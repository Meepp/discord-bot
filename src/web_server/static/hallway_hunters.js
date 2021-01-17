let canvas = document.getElementById("canvas");
canvas.width = 1000;
canvas.height = 600;
let context = canvas.getContext("2d");
context.imageSmoothingEnabled = true;

const TILE_SIZE = 16;

let socket = io();

socket.on("join", (data) => {
    console.log(`${data} joined the room.`);
});

$('#messageform').submit(function(e) {
    e.preventDefault(); // prevents page reloading
    let m = $('#m');
    data = {
        "message": m.val(),
        "room": $('#roomid').val(),
        "username": $('#username').val()
    };
    socket.emit('chat message', data);
    m.val('');
    return false;
});

socket.on("chat message", (data) => {
    let messages = $('#messages');
    messages.append($('<li class="chat-message-entry">').text(data.username + ": " + data.message));
    document.getElementById("messages").lastChild.scrollIntoView();
});

function loadMainContent(gameWrapper) {
    let divs = document.getElementsByClassName("main-content");
    Array.from(divs).forEach((div) => {
        div.style.display = "none";
    });

    document.getElementById(gameWrapper).style.display = "flex";
}

function getRelativeMousePosition(canvas, evt) {
    let rect = canvas.getBoundingClientRect();
    return {
        x: evt.clientX - rect.left,
        y: evt.clientY - rect.top
    };
}

function HallwayHunters() {
    this.state = {
        board_size: 30,
        player_data: {
            name: "",
            position: {
                x: 0,
                y: 0
            },
            pre_move: {
                x: 0,
                y: 0
            },
            cooldown: 0,
            cooldown_timer: 0,
        }
    };
    this.fadeMessages = [];
    this.tiles = {};

    this.setState = function(data) {
        this.state = {
            ...data,
        };
    };

    this.MESSAGE_HEIGHT = 40;
    this.drawFadeMessages = function() {
        let origHeight = 100;
        if (this.fadeMessages.length > 0) {
            if (this.fadeMessages[0].ticks < 0) {
                this.fadeMessages = this.fadeMessages.slice(1);
            } else {
                origHeight -= (1 - Math.min(1, this.fadeMessages[0].ticks / 30)) * this.MESSAGE_HEIGHT * 1.5;
            }
        }
        let n_visible = Math.min(5, this.fadeMessages.length);
        for (let i = 0; i < n_visible; i++) {
            let fm = this.fadeMessages[i];
            let percent = Math.min(1, fm.ticks / 30);

            context.font = `${this.MESSAGE_HEIGHT}px Arial`;
            context.strokeStyle = `rgba(0, 0, 0, ${percent})`;
            context.lineWidth = 0.5;
            context.fillStyle = `rgba(165, 70, 50, ${percent})`;

            let len = context.measureText(fm.message);
            context.fillText(fm.message, 480 - len.width / 2, origHeight + i * this.MESSAGE_HEIGHT * 1.5);
            context.strokeText(fm.message, 480 - len.width / 2, origHeight + i * this.MESSAGE_HEIGHT * 1.5);
            context.stroke();

            fm.ticks--;
        }
    }
}


// Game rendering stuff
function render() {
    // Resizing the canvas should overwrite the width and height variables
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;

    context.clearRect(0, 0, canvas.width, canvas.height);

    // Compute the offset for all tiles, to center rendering on the player.
    const xOffset = -game.state.player_data.position.x + canvas.width / 2 - TILE_SIZE / 2;
    const yOffset = -game.state.player_data.position.y + canvas.height / 2 - TILE_SIZE / 2;

    // Draw tiles
    for (let x = 0; x < game.state.board_size; x++) {
        for (let y = 0; y < game.state.board_size; y++) {
            let imageData = game.tiles[game.state.board[x][y].image];
            context.putImageData(imageData, x * TILE_SIZE + xOffset, y * TILE_SIZE + yOffset);
        }
    }

    context.putImageData(game.tiles["character_blue"], game.state.player_data.position.x + xOffset, game.state.player_data.position.y + yOffset);

    game.drawFadeMessages();
}

let images = {};
let audioFiles = {};
let game = new HallwayHunters();

function split_sheet() {
    canvas = document.createElement("canvas");
    canvas.width = this.width;
    canvas.height = this.height;
    context = canvas.getContext("2d");
    context.drawImage(tileSet, 0, 0);

    const S = TILE_SIZE;

    game.tiles["corner_tl"] = context.getImageData(0 * S, 0 * S, S, S);
    game.tiles["edge_t"]    = context.getImageData(1 * S, 0 * S, S, S);
    game.tiles["corner_tr"] = context.getImageData(2 * S, 0 * S, S, S);
    game.tiles["edge_l"]    = context.getImageData(0 * S, 1 * S, S, S);
    game.tiles["center"]    = context.getImageData(1 * S, 1 * S, S, S);
    game.tiles["edge_r"]    = context.getImageData(2 * S, 1 * S, S, S);
    game.tiles["corner_bl"] = context.getImageData(0 * S, 2 * S, S, S);
    game.tiles["edge_b"]    = context.getImageData(1 * S, 2 * S, S, S);
    game.tiles["corner_br"] = context.getImageData(2 * S, 2 * S, S, S);

    game.tiles["character_blue"] = context.getImageData(19 * S, 7 * S, S, S);
    game.tiles["character_red"] = context.getImageData(20 * S, 7 * S, S, S);
    game.tiles["character_green"] = context.getImageData(21 * S, 7 * S, S, S);
    game.tiles["character_purple"] = context.getImageData(22 * S, 7 * S, S, S);
    game.tiles["character_black"] = context.getImageData(23 * S, 7 * S, S, S);
}

let tileSet = null;
function initialize() {
    /*
     * Preload all images to reduce traffic later.
     */
    tileSet = new Image();
    tileSet.onload = split_sheet;
    tileSet.src = "images/tiles/dungeon_sheet.png";

    /*
     * Register all socket.io functions to the game object.
     */
    socket.on("game_state", (data) => {
        game.setState(data);

        if (!game.state.started) {
            // Lobby stuff
            let userList = $(".user-list");
            userList.empty();
            data.players.forEach(player => {
                userList.append(`
                    <div class="user-entry">
                    <div class="user-entry-name">${player.name}</div>
                    <div class="user-entry-balance">${CURRENCY}${player.balance}</div>
                    <div class="user-entry-ready">${player.ready ? "Ready" : "Not Ready"}</div>
                    </div>
                `);
            });

            let settings = document.getElementById("room-settings");
            settings.innerHTML = `<div>   
            </div>`;
        }

    });
    socket.on("message", (data) => {
        game.fadeMessages.push({
            message: data,
            ticks: 120
        });
    });

    // Request game state on initialization.
    socket.emit("game_state", {
        "room": ROOM_ID
    });
}

function sendAction(action, value) {
    socket.emit("action", {"room": ROOM_ID, "action": action, "value": value})
}

let has_started = false;
socket.on("start", () => {
    loadMainContent("game-wrapper");
    if (!has_started) {
        has_started = true;
        setInterval(render, 1000 / 60);
    }
});
initialize();

function startRoom() {
    if (!game.state.started) {
        socket.emit("start", {
            room: ROOM_ID
        });
    }
}

function toggleReady() {
    socket.emit("start", {
        room: ROOM_ID
    });
}

socket.on("start", () => {
    // What to do on start for all players
});

socket.on("message", (data) => {
    let log = document.getElementById("event-log");
    log.innerHTML += `
    <div class="event-log-entry">
        <div class="event-log-date">${new Date().toLocaleTimeString()}</div>
        <div class="event-log-value">${data}</div>
    </div>`;

    log.lastChild.scrollIntoView();
});

function changeSettings() {
    let data = {
        room_id: ROOM_ID,
        settings: {

        }
    };
    socket.emit("change settings", data)
}

document.addEventListener("keydown", (ev) => {
    // Game inputs
});


socket.emit("join", {
    "room": ROOM_ID,
});


