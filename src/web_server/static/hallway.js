let canvas = document.getElementById("canvas");
canvas.width = 1000;
canvas.height = 600;
let context = canvas.getContext("2d");
context.imageSmoothingEnabled = true;

const TILE_SIZE = 64;
const TILE_PADDING = 0;

let socket = io("/hallway");

socket.on("join", (data) => {
    console.log(`${data} joined the room.`);
});

$('#messageform').submit(function (e) {
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
        players: [],
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
    this.selected = {
        x: 0,
        y: 0,
    };
    this.mouseDown = false;

    this.setState = function (data) {
        this.state = {
            ...data,
        };
    };

    this.MESSAGE_HEIGHT = 40;
    this.drawFadeMessages = function () {
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
    };

    this.onMove = function (e) {
        if (!game.mouseDown) return;
        const pos = getRelativeMousePosition(canvas, e);

        // Compute the offset for all tiles, to center rendering on the player.
        const S = (TILE_SIZE + TILE_PADDING);
        const xOffset = -game.state.player_data.position.x * S + canvas.width / 2;
        const yOffset = -game.state.player_data.position.y * S + canvas.height / 2;


        game.selected = {
            x: Math.round((pos.x - xOffset) / S),
            y: Math.round((pos.y - yOffset) / S)
        }
    }
}


// Game rendering stuff
function render() {
    // Resizing the canvas should overwrite the width and height variables
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;

    context.clearRect(0, 0, canvas.width, canvas.height);
    // context.fillStyle = "#EEEEEE";
    // context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(game.tiles["floor"],0, 0, canvas.width, canvas.height);

    // Compute the offset for all tiles, to center rendering on the player.
    const S = (TILE_SIZE + TILE_PADDING);
    const xOffset = -game.state.player_data.position.x * S + canvas.width / 2 - TILE_SIZE / 2;
    const yOffset = -game.state.player_data.position.y * S + canvas.height / 2 - TILE_SIZE / 2;


    // Draw selected tile by means of darker square
    context.fillStyle = "#3c5978";
    context.fillRect(
        game.selected.x * S + xOffset - TILE_PADDING,
        game.selected.y * S + yOffset  - TILE_PADDING,
        S + TILE_PADDING,
        S + TILE_PADDING
    );


    // Draw tiles
    for (let x = 0; x < game.state.board_size; x++) {
        for (let y = 0; y < game.state.board_size; y++) {
            context.drawImage(
                game.tiles[game.state.board[x][y].image],
                x * S + xOffset,
                y * S + yOffset
            );
        }
    }

    game.state.players.forEach((player) => {
        const x = player.position.x * S + xOffset;
        const y = player.position.y * S + yOffset;
        // context.translate(x, y);
        // context.rotate(player.rotation);
        context.drawImage(game.tiles[player.name], x, y);
        // context.rotate(player.rotation);
        // context.translate(x, y);
    });

    game.drawFadeMessages();
}

let images = {};
let audioFiles = {};
let game = new HallwayHunters();

function split_sheet() {
    const scale = TILE_SIZE / 16;
    let canvas = document.createElement("canvas");
    canvas.width = this.width * scale;
    canvas.height = this.height * scale;
    let context = canvas.getContext("2d");
    context.clearRect(0,0, canvas.width, canvas.height);
    context.webkitImageSmoothingEnabled = false;
    context.mozImageSmoothingEnabled = false;
    context.imageSmoothingEnabled = false;

    context.scale(scale, scale);
    context.drawImage(tileSet, 0, 0);

    const S = TILE_SIZE;

    game.tiles["edge_b"]        = context.getImageData(6 * S, 1 * S, S, S);
    game.tiles["edge_b_top"]    = context.getImageData(6 * S, 0 * S, S, S);
    game.tiles["edge_b_alt1"]        = context.getImageData(8 * S, 5 * S, S, S);
    game.tiles["edge_b_alt1_top"]    = context.getImageData(8 * S, 4 * S, S, S);
    game.tiles["edge_b_alt2"]        = context.getImageData(9 * S, 5 * S, S, S);
    game.tiles["edge_b_alt2_top"]    = context.getImageData(9 * S, 4 * S, S, S);

    game.tiles["corner_br"]     = context.getImageData(9 * S, 3 * S, S, S);
    game.tiles["corner_br_top"] = context.getImageData(9 * S, 2 * S, S, S);

    game.tiles["corner_bl"]     = context.getImageData(8 * S, 3 * S, S, S);
    game.tiles["corner_bl_top"] = context.getImageData(8 * S, 2 * S, S, S);

    game.tiles["corner_tr"]    = context.getImageData(9 * S, 1 * S, S, S);
    game.tiles["corner_tr_top"] = context.getImageData(9 * S, 0 * S, S, S);

    game.tiles["corner_tl"]    = context.getImageData(8 * S, 1 * S, S, S);
    game.tiles["corner_tl_top"] = context.getImageData(8 * S, 0 * S, S, S);

    game.tiles["inner_corner_br"]     = context.getImageData(7 * S, 3 * S, S, S);
    game.tiles["inner_corner_br_top"] = context.getImageData(7 * S, 2 * S, S, S);

    game.tiles["inner_corner_bl"]     = context.getImageData(5 * S, 3 * S, S, S);
    game.tiles["inner_corner_bl_top"] = context.getImageData(5 * S, 2 * S, S, S);

    game.tiles["inner_corner_tr"]     = context.getImageData(7 * S, 1 * S, S, S);
    game.tiles["inner_corner_tr_top"] = context.getImageData(7 * S, 0 * S, S, S);

    game.tiles["inner_corner_tl"]     = context.getImageData(5 * S, 1 * S, S, S);
    game.tiles["inner_corner_tl_top"] = context.getImageData(5 * S, 0 * S, S, S);

    game.tiles["edge_t"]        = context.getImageData(6 * S, 3 * S, S, S);
    game.tiles["edge_t_top"]    = context.getImageData(5 * S, 3 * S, S, S);

    game.tiles["edge_r"]    = context.getImageData(5 * S, 2 * S, S, S);
    game.tiles["void"]      = context.getImageData(1 * S, 1 * S, S, S);
    game.tiles["edge_l"]    = context.getImageData(7 * S, 2 * S, S, S);
    game.tiles["edge_t"]    = context.getImageData(6 * S, 3 * S, S, S);

    game.tiles["floor"]      = context.getImageData(6 * S, 2 * S, S, S);
    game.tiles["wall_test"] = context.getImageData(6 * S, 1 * S, S, S);
    game.tiles["door"] = context.getImageData(7 * S, 7 * S, S, S);

    game.tiles["Demolisher"]   = context.getImageData(19 * S, 7 * S, S, S);
    game.tiles["character_red"]    = context.getImageData(20 * S, 7 * S, S, S);
    game.tiles["character_green"]  = context.getImageData(21 * S, 7 * S, S, S);
    game.tiles["character_purple"] = context.getImageData(22 * S, 7 * S, S, S);
    game.tiles["character_black"]  = context.getImageData(23 * S, 7 * S, S, S);

    for (const [title, data] of Object.entries(game.tiles)) {
        canvas.width = data.width;
        canvas.height = data.height;
        context.putImageData(data, 0, 0);

        let image = new Image();
        image.src = canvas.toDataURL();
        game.tiles[title] = image;
    }
}

let tileSet = null;
function initialize() {
    /*
     * Preload all images to reduce traffic later.
     */
    tileSet = new Image();
    tileSet.onload = split_sheet;
    tileSet.src = "/static/images/tiles/dungeon_sheet.png";

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
                    <div class="user-entry-name">${player.username}</div>
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

function sendAction() {
    let data = {
        room: ROOM_ID,
        move: game.selected,
    };
    console.log(data)
    console.log(game.state.player_data.position)
    socket.emit("action", data);
}

let has_started = false;
socket.on("start", () => {
    loadMainContent("game-wrapper");
    if (!has_started) {
        has_started = true;
        setInterval(render, 1000 / 60);
    }
});

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



function changeSettings() {
    let data = {
        room_id: ROOM_ID,
        settings: {}
    };
    socket.emit("change settings", data)
}

function sendSelected() {
    let data = {
        room: ROOM_ID,
        move: game.selected,
    };
    socket.emit("move", data);
}

canvas.addEventListener("mousemove", game.onMove);
canvas.addEventListener("mousedown", (e) => {game.mouseDown = true; game.onMove(e)});
canvas.addEventListener("mouseup", (e) => {
    game.mouseDown = false;

    sendSelected()
});
document.addEventListener("keydown", (ev) => {
    // Game inputs
    if (ev.key === "ArrowUp") {
        game.selected = {...game.state.player_data.position};
        game.selected.y -= 1;
        sendSelected();
    } else if (ev.key === "ArrowDown") {
        game.selected = {...game.state.player_data.position};
        game.selected.y += 1;
        sendSelected();
    } else if (ev.key === "ArrowLeft") {
        game.selected = {...game.state.player_data.position};
        game.selected.x -= 1;
        sendSelected();
    } else if (ev.key === "ArrowRight") {
        game.selected = {...game.state.player_data.position};
        game.selected.x += 1;
        sendSelected();
    } else if (ev.key === "c") {

        game.selected = {...game.state.player_data.position};
        sendAction()
    }

});

console.log("Emitting join");
socket.emit("join", {
    "room": ROOM_ID,
});


initialize();
