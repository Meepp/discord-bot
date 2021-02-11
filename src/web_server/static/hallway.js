let canvas = document.getElementById("canvas");
let context = canvas.getContext("2d");
context.webkitImageSmoothingEnabled = false;
context.mozImageSmoothingEnabled = false;
context.imageSmoothingEnabled = false;

const TILE_SIZE = 48;
const TILE_PADDING = 0;
const FRAMES_PER_ANIMATION = 6;

let socket = io("/hallway");

socket.on("join", (data) => {
    console.log(`${data} joined the room.`);
});

let startTime;
setInterval(function () {
    startTime = Date.now();
    socket.emit('ping');
}, 2000);

socket.on('pong', function () {
    console.log("Ping: " + (Date.now() - startTime) + "ms");
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

socket.on("command error", (data) => {
    let messages = $('#messages');
    console.log(data)
    console.log(messages)
    messages.append($('<li class="chat-message-entry" style="color:red">').text("Error: " + data));
    document.getElementById("messages").lastChild.scrollIntoView();
})

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
        all_players: [],
        player_data: {
            name: "",
            position: {
                x: 0,
                y: 0
            },
            previous_position: {
                x: 0,
                y: 0
            },
            pre_move: {
                x: 0,
                y: 0
            },
            is_moving: false,
            cooldown: 0,
            cooldown_timer: 0,
            movement_cooldown: 0,
            movement_timer: 0,
            sprint: 0,
            sprint_timer: 0,
            objective: {
                position: {
                    x: 10,
                    y: 10,
                }
            },
            stored_items: [{
                name: "",
            }],
            kill_timer: 0,
            kill_cooldown: 0,
            passives: [{
                name: "",
                time: 0,
                total_time: 0
            }]
        },
        visible_tiles: [
            {x: 0, y: 0, tile: {}}
        ],
        board: [],

    };
    this.lookup = {};
    this.fadeMessages = [];
    this.tiles = {};
    this.animations = {};

    this.setState = function (data) {
        this.state = {
            ...this.state,
            ...data
        };

        this.lookup = {};
        this.state.visible_tiles.forEach((obj) => {
            this.state.board[obj.x][obj.y] = obj.tile;
            if (this.lookup[obj.x] === undefined) {
                this.lookup[obj.x] = {};
            }
            this.lookup[obj.x][obj.y] = true;
        });
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
}


function renderMinimap() {
    const minimap_pixel_size = 2;
    const size = game.state.board_size;
    const mm_size = size * minimap_pixel_size;

    const mm_offset_x = canvas.width - mm_size;
    const mm_offset_y = 0;
    context.clearRect(mm_offset_x, mm_offset_y, mm_size, mm_size);
    for (let x = 0; x < size; x++) {
        for (let y = 0; y < size; y++) {
            const tile = game.state.board[x][y];

            if (tile.movement_allowed) {
                context.fillStyle = "#bbb";
            } else if (!tile.opaque) {
                context.fillStyle = "#7e7e7e";
            } else {
                context.fillStyle = "#454545";
            }

            if (game.state.player_data.position.x === x && game.state.player_data.position.y === y) {
                context.fillStyle = "#ec2b3c";
            }

            if (game.state.player_data.objective.x === x && game.state.player_data.objective.y === y) {
                context.fillStyle = "#63ee52";
            }

            context.fillRect(mm_offset_x + x * minimap_pixel_size, mm_offset_y + y * minimap_pixel_size, minimap_pixel_size, minimap_pixel_size);
        }
    }
}

function getAnimationFrame(animation) {
    // If the animation is active, or the animation is not yet finished and it has to finish.
    if (animation.active || (animation.finishAnimation && animation.currentSprite !== 0)) {
        // Increment amount of frames waiting for next sprite
        animation.frameNumber = (animation.frameNumber + 1) % FRAMES_PER_ANIMATION;
        if (animation.frameNumber === 0) {
            // Increment sprite
            animation.currentSprite = (animation.currentSprite + 1) % animation.sprites.length;
        }
    }
    return animation.sprites[animation.currentSprite];
}

function directionToVector(direction, number) {
    if (direction === 0) {
        return {x: 0, y: -number};
    } else if (direction === 90) {
        return {x: number, y: 0};
    } else if (direction === 180) {
        return {x: 0, y: number};
    } else {
        return {x: -number, y: 0};
    }
}


function renderKillCam() {
    const x = 500;
    const y = 500;

    let killPassive = game.state.player_data.passives.filter((item) => {
        return (item.name === "kill")
    });
    if (killPassive.length === 0) return;
    killPassive = killPassive[0];

    const cooldown = killPassive.time / killPassive.total_time;
    context.lineWidth = 20;
    context.strokeStyle = "#418eb0";
    context.beginPath();
    context.arc(x, y, 50, 0, 2 * Math.PI);
    context.stroke();

    context.lineWidth = 18;
    context.strokeStyle = "#3f3656";
    context.beginPath();
    context.arc(x, y, 50, 0, cooldown * 2 * Math.PI);
    context.stroke();

    const animationName = game.state.player_data.killing.name + "_" + game.state.player_data.killing.direction;
    const animation = game.animations[animationName];
    const sprite = animation.sprites[animation.currentSprite];
    context.drawImage(sprite, x - TILE_SIZE / 2, y - TILE_SIZE / 2);
}

function drawPlayer(player, S, xOffset, yOffset) {
    const interpolation = -(player.movement_timer / player.movement_cooldown);
    const vector = directionToVector(player.direction, interpolation * S);
    const x = player.position.x * S + xOffset + Math.round(vector.x);
    const y = player.position.y * S + yOffset + Math.round(vector.y);

    // If the player is not moving, reset its animation frame to beginning.
    const animationName = player.name + "_" + player.direction;
    const animation = game.animations[animationName];

    // Player animation is bound to moving
    animation.active = player.is_moving;
    if (!player.is_moving) {
        // Set player frame to this when not moving
        animation.frameNumber = FRAMES_PER_ANIMATION - 2;
        animation.currentSprite = 0;
    }
    const sprite = getAnimationFrame(animation);

    context.drawImage(sprite, x, y);
    if (player.item !== null) {
        context.drawImage(game.tiles[player.item.name], x, y - S / 2 - 7);
    }
}

function renderCooldowns() {
    // TODO: Refactor this to work more easily with more different cooldowns.
    const pd = game.state.player_data;
    const timers = [[
        pd.cooldown_timer, pd.cooldown, "C"
    ], [
        pd.sprint_timer, pd.sprint, "X"
    ], [
        pd.kill_timer, pd.kill_cooldown, "Z"
    ]];

    timers.map((timer, i) => {
        const cooldown = timer[0] / timer[1];
        context.lineWidth = 20;
        context.strokeStyle = "#418eb0";
        context.beginPath();
        context.arc(75 + 150 * i, canvas.height - 75, 50, 0, 2 * Math.PI);
        context.stroke();

        context.lineWidth = 18;
        context.strokeStyle = "#3f3656";
        context.beginPath();
        context.arc(75 + 150 * i, canvas.height - 75, 50, 0, cooldown * 2 * Math.PI);
        context.stroke();

        const fontSize = 50;
        context.font = fontSize + "px Arial";
        context.fillStyle = "#fff";
        if (keyState[timer[2].toLowerCase()])
            context.fillStyle = "#AAA";
        const width = context.measureText(timer[2]).width;
        context.fillText(timer[2], 75 + 150 * i - width / 2, canvas.height - 75 + fontSize / 3);
    })

}

function renderStorage() {
    const padding = 10;
    const S = (TILE_SIZE + TILE_PADDING);
    const itemWidth = S + 2 * padding;
    const W = game.state.player_data.stored_items.length * itemWidth;
    const H = S + 2 * padding;

    // Not opaque item list
    context.fillStyle = "rgba(255, 255, 255, 0.1)";
    context.fillRect(0, 0, W, H);
    game.state.player_data.stored_items.map((item, index) => {
        context.drawImage(
            game.tiles[item.name],
            padding + index * itemWidth,
            padding
        );
    })
}

function handleInput() {
    if (keyState["ArrowUp"]) {
        sendMove({x: 0, y: -1});
    } else if (keyState["ArrowDown"]) {
        sendMove({x: 0, y: 1});
    } else if (keyState["ArrowLeft"]) {
        sendMove({x: -1, y: 0});
    } else if (keyState["ArrowRight"]) {
        sendMove({x: 1, y: 0});
    }

    // TODO: Refactor this to not be dumb (maybe get valid actions from server?)
    if (keyState["c"]) {
        sendAction("c");
    }
    if (keyState["x"]) {
        sendAction("x");
    }
    if (keyState["z"]) {
        sendAction("z");
    }
}

function extracted(x, y, sprite, S, xOffset, yOffset) {

    context.drawImage(
        sprite,
        x * S + xOffset,
        y * S + yOffset
    );

    // Draw item on top of tile if there is an item on this tile.
    if (game.state.board[x][y].item !== null) {
        context.drawImage(
            game.tiles[game.state.board[x][y].item.name],
            x * S + xOffset,
            y * S + yOffset
        );
    }

    if (game.lookup[x] === undefined || !game.lookup[x][y]) {
        context.fillRect(x * S + xOffset, y * S + yOffset, TILE_SIZE, TILE_SIZE)
    }
}

function renderTiles(S, xOffset, yOffset) {
    context.fillStyle = "rgb(0, 0, 0, 0.3)";


    for (let x = 0; x < game.state.board_size; x++) {
        if (x * S + xOffset + TILE_SIZE < 0) continue;
        if (x * S + xOffset > canvas.width) break;
        for (let y = 0; y < game.state.board_size; y++) {
            if (y * S + yOffset + TILE_SIZE < 0) continue;
            if (y * S + yOffset > canvas.height) break;
            const tile = game.state.board[x][y];
            const animation = game.animations[tile.image];
            let sprite;
            if (animation === undefined) {
                sprite = game.tiles[tile.image];
            } else {
                animation.active = tile.animation_ticks > 0;
                if (animation.active) {
                    animation.finishAnimation = tile.finish_animation;
                }
                sprite = getAnimationFrame(animation);
            }

            extracted(x, y, sprite, S, xOffset, yOffset);
        }
    }
}

// Game rendering stuff
function gameLoop() {
    handleInput();

    // Resizing the canvas should overwrite the width and height variables
    // It has to be a multiple of 2 to remove artifacts around the tilesets
    canvas.width = Math.round(canvas.clientWidth / 2) * 2;
    canvas.height = Math.round(canvas.clientHeight / 2) * 2;

    // Clear the canvas and fill with floor tile color.
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.drawImage(game.tiles["floor"], 0, 0, canvas.width, canvas.height);

    // Compute the offset for all tiles, to center rendering on the player.
    const S = (TILE_SIZE + TILE_PADDING);

    const interpolation = game.state.player_data.movement_timer / game.state.player_data.movement_cooldown;
    const vector = directionToVector(game.state.player_data.direction, interpolation * S);
    const xOffset = -game.state.player_data.position.x * S + canvas.width / 2 - TILE_SIZE / 2 + Math.round(vector.x);
    const yOffset = -game.state.player_data.position.y * S + canvas.height / 2 - TILE_SIZE / 2 + Math.round(vector.y);

    // Draw tiles
    renderTiles(S, xOffset, yOffset);

    game.state.players.forEach((player) => {
        drawPlayer(player, S, xOffset, yOffset);
    });

    // renderMinimap();
    renderStorage();
    renderCooldowns();
    renderKillCam();
}

let game = new HallwayHunters();


function createAnimation(sprites) {
    return {
        sprites: sprites,
        frameNumber: 0,
        currentSprite: 0,
        active: false,
        finishAnimation: false,
    };
}

function split_sheet() {
    const scale = TILE_SIZE / 16;
    let canvas = document.createElement("canvas");
    canvas.className = "disable-anti-aliasing";
    canvas.width = this.width * scale;
    canvas.height = this.height * scale;
    console.log(this.width, this.height, canvas);
    let context = canvas.getContext("2d");

    context.clearRect(0, 0, canvas.width, canvas.height);
    context.webkitImageSmoothingEnabled = false;
    context.mozImageSmoothingEnabled = false;
    context.imageSmoothingEnabled = false;

    context.scale(scale, scale);
    context.drawImage(tileSet, 0, 0);

    const S = TILE_SIZE;

    game.tiles["edge_b"] = context.getImageData(6 * S, 1 * S, S, S);
    game.tiles["edge_b_top"] = context.getImageData(6 * S, 0 * S, S, S);
    game.tiles["edge_b_alt1"] = context.getImageData(8 * S, 5 * S, S, S);
    game.tiles["edge_b_alt1_top"] = context.getImageData(8 * S, 4 * S, S, S);
    game.tiles["edge_b_alt2"] = context.getImageData(9 * S, 5 * S, S, S);
    game.tiles["edge_b_alt2_top"] = context.getImageData(9 * S, 4 * S, S, S);
    game.tiles["edge_b_alt3"] = context.getImageData(5 * S, 4 * S, S, S);

    game.tiles["corner_br"] = context.getImageData(9 * S, 3 * S, S, S);
    game.tiles["corner_br_top"] = context.getImageData(9 * S, 2 * S, S, S);

    game.tiles["corner_bl"] = context.getImageData(8 * S, 3 * S, S, S);
    game.tiles["corner_bl_top"] = context.getImageData(8 * S, 2 * S, S, S);

    game.tiles["corner_tr"] = context.getImageData(9 * S, 1 * S, S, S);
    game.tiles["corner_tr_top"] = context.getImageData(9 * S, 0 * S, S, S);

    game.tiles["corner_tl"] = context.getImageData(8 * S, 1 * S, S, S);
    game.tiles["corner_tl_top"] = context.getImageData(8 * S, 0 * S, S, S);

    game.tiles["inner_corner_br"] = context.getImageData(7 * S, 3 * S, S, S);
    game.tiles["inner_corner_br_top"] = context.getImageData(7 * S, 2 * S, S, S);

    game.tiles["inner_corner_bl"] = context.getImageData(5 * S, 3 * S, S, S);
    game.tiles["inner_corner_bl_top"] = context.getImageData(5 * S, 2 * S, S, S);

    game.tiles["inner_corner_tr"] = context.getImageData(7 * S, 1 * S, S, S);
    game.tiles["inner_corner_tr_top"] = context.getImageData(7 * S, 0 * S, S, S);

    game.tiles["inner_corner_tl"] = context.getImageData(5 * S, 1 * S, S, S);
    game.tiles["inner_corner_tl_top"] = context.getImageData(5 * S, 0 * S, S, S);

    game.tiles["edge_t"] = context.getImageData(6 * S, 3 * S, S, S);
    game.tiles["edge_t_alt1"] = context.getImageData(7 * S, 5 * S, S, S);

    game.tiles["edge_l"] = context.getImageData(7 * S, 2 * S, S, S);
    game.tiles["edge_l_alt1"] = context.getImageData(6 * S, 4 * S, S, S);
    game.tiles["edge_l_alt2"] = context.getImageData(7 * S, 4 * S, S, S);

    game.tiles["edge_r"] = context.getImageData(5 * S, 2 * S, S, S);
    game.tiles["void"] = context.getImageData(1 * S, 1 * S, S, S);
    game.tiles["edge_t"] = context.getImageData(6 * S, 3 * S, S, S);

    game.tiles["floor"] = context.getImageData(6 * S, 2 * S, S, S);
    game.tiles["wall_test"] = context.getImageData(6 * S, 1 * S, S, S);

    game.tiles["door"] = context.getImageData(7 * S, 7 * S, S, S);
    game.tiles["ladder"] = context.getImageData(15 * S, 8 * S, S, S);

    ["red", "blue", "green", "purple", "black"].map((color, row) => {
        for (let i = 0; i < 3; i++) {
            game.tiles[color + "_90_" + i] = context.getImageData(i * S, (11 + row) * S, S, S);
            game.tiles[color + "_270_" + i] = context.getImageData((i + 3) * S, (11 + row) * S, S, S);
            game.tiles[color + "_180_" + i] = context.getImageData((i + 6) * S, (11 + row) * S, S, S);
            game.tiles[color + "_0_" + i] = context.getImageData((i + 9) * S, (11 + row) * S, S, S);
        }
        for (let i = 0; i < 6; i++) {
            game.tiles["chest_" + color + "_" + i] = context.getImageData((i + 12) * S, (11 + row) * S, S, S);
        }
    });

    ["blue", "red", "green", "purple", "black"].map((color, i) => {
        game.tiles["collector_" + color] = context.getImageData((19 + i) * S, 6 * S, S, S);
    });

    for (let i = 0; i < 4; i++) {
        game.tiles["rubbish_" + i] = context.getImageData((i + 15) * S, 7 * S, S, S);
    }

    for (const [title, data] of Object.entries(game.tiles)) {
        canvas.width = data.width;
        canvas.height = data.height;
        context.putImageData(data, 0, 0);

        let image = new Image();
        image.src = canvas.toDataURL();
        game.tiles[title] = image;
    }

    ["red", "blue", "green", "purple", "black"].forEach(color => {
        ["0", "90", "180", "270"].forEach(rotation => {
            game.animations[`${color}_${rotation}`] = createAnimation([
                game.tiles[`${color}_${rotation}_0`],
                game.tiles[`${color}_${rotation}_1`],
                game.tiles[`${color}_${rotation}_0`],
                game.tiles[`${color}_${rotation}_2`],
            ]);
        });

        game.animations[`chest_${color}`] = createAnimation([
            game.tiles[`chest_${color}_0`],
            game.tiles[`chest_${color}_1`],
            game.tiles[`chest_${color}_2`],
            game.tiles[`chest_${color}_3`],
            game.tiles[`chest_${color}_4`],
            game.tiles[`chest_${color}_5`],
            game.tiles[`chest_${color}_5`],
            game.tiles[`chest_${color}_5`],
            game.tiles[`chest_${color}_4`],
            game.tiles[`chest_${color}_3`],
            game.tiles[`chest_${color}_2`],
            game.tiles[`chest_${color}_1`],
            game.tiles[`chest_${color}_0`]
        ]);
        // Always close the chest.
        game.animations[`chest_${color}`].finishAnimation = true;
    });

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
        console.log(game)
        if (!game.state.started) {
            // Lobby stuff
            let userList = $(".user-list");
            userList.empty();
            console.log(data)
            data.all_players.forEach(player => {
                console.log(player)
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
        } else {
            let playerList = $(".player-list");
            playerList.empty();
            console.log(data)
            data.all_players.forEach(player => {
                playerList.append(`
                    <div class="user-entry">
                    <div class="user-entry-name">${player.username}</div>
                    <div class="user-entry-ready">${player.stored_items.length}</div>
                    </div>
                `);
            });
        }

    });
    socket.on("message", (data) => {
        console.log(data);
        // game.fadeMessages.push({
        //     message: data,
        //     ticks: 120
        // });
    });

    // Request game state on initialization.
    socket.emit("game_state", {
        "room": ROOM_ID
    });
}

function sendAction(action) {
    let data = {
        room: ROOM_ID,
        action: action
    };
    socket.emit("action", data);
}

let has_started = false;
socket.on("start", () => {
    loadMainContent("game-wrapper");
    if (!has_started) {
        has_started = true;
        setInterval(gameLoop, 1000 / 60);
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
    const cls = document.getElementById("class-selector").value;
    socket.emit("start", {
        room: ROOM_ID,
        player_class: cls,
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

function sendMove(move) {
    let data = {
        room: ROOM_ID,
        move: move,
    };
    socket.emit("move", data);
}

let keyState = {};
document.addEventListener("keydown", (ev) => {
    keyState[ev.key] = true;
});
document.addEventListener("keyup", (ev) => {
    keyState[ev.key] = false;
    sendMove({x: 0, y: 0});
});

socket.emit("join", {
    "room": ROOM_ID,
});


initialize();
