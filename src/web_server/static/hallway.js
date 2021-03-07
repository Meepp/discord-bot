let canvas = document.getElementById("canvas");
let context = canvas.getContext("2d");
context.webkitImageSmoothingEnabled = false;
context.mozImageSmoothingEnabled = false;
context.imageSmoothingEnabled = false;

const FPS_INTERVAL = 1000 / 60;

class RollingAverage {
    constructor(n) {
        this.values = [];
        this.n = n;
    }

    put(value) {
        this.values.unshift(value);
        this.values = this.values.slice(0, this.n);
    }

    get() {
        return this.values.reduce((a, b) => a + b, 0) / this.values.length;
    }
}


class Player {
    constructor(image) {
        this.renderable = true;
        this.x = 0;
        this.y = 0;
        this.direction = 0;
        this.moving = false;

        this.name = new DrawableText(0, 0);
        // Default values
        this.name.fontSize = 6;
        this.name.color = "#fff";
        this.name.borderColor = "#777";

        this.scoreText = new DrawableText(0,0);
        this.scoreText.fontSize = 15;
        this.score = -1;

        // Only useful when you are the scout
        this.cameraPosition = new Point(0, 0);
        this.cameraTiles = null;

        const padding = 10;
        const radius = 30;
        this.zCooldown = new CircularCooldown(padding + radius * 2, gameView.height - padding, radius);
        this.zCooldown.textObject.text = "Z";
        this.xCooldown = new CircularCooldown(padding + radius * 5, gameView.height - padding, radius);
        this.xCooldown.textObject.text = "X";
        this.cCooldown = new CircularCooldown(padding + radius * 8, gameView.height - padding, radius);
        this.cCooldown.textObject.text = "C";

        this.item = null;

        // Fallback
        this.sprite = new SpriteTile(image);
        this.walkAnimations = [
            null,
            null,
            null,
            null
        ];
        this.idleAnimations = [
            null,
            null,
            null,
            null
        ];
    }

    update(data) {
        this.x = data.position.x;
        this.y = data.position.y;
        this.moving = data.is_moving;
        this.direction = data.direction;

        this.score = data.stored_items.length;

        if (data.item !== null && data.item !== undefined)
            this.item = new SpriteTile(game.tiles[data.item.name]);
        else
            this.item = null;

        // Update the camera display if you receive camera updates (only relevant for scout class)
        if (data.camera_list !== undefined && data.camera_list.length > 0) {
            // Store this position to know where to render players relative to their own position
            this.cameraPosition.x = data.camera_list[0].x;
            this.cameraPosition.y = data.camera_list[0].y;

            for (let i = 0; i < data.camera_list.length; i++) {
                let tile = data.camera_list[i].tile;
                let image = game.tiles[tile.image];
                this.cameraTiles[i].setImage(image);
                let item = this.cameraTiles[i].item;
                // Update the item if
                if (tile.item !== null) {
                    let itemImage = game.tiles[tile.item.name];
                    item.renderable = true;
                    item.setImage(itemImage);
                } else {
                    item.renderable = false;
                }
            }

            // Update players which are visible on camera
            for (const [colour, player] of Object.entries(game.players)) {
                let xDiff = player.x - this.cameraPosition.x;
                let yDiff = player.y - this.cameraPosition.y;
                if (xDiff >= 0 && xDiff < 5 && yDiff > -1 && yDiff <= 4) {
                    cameraView.players[colour].update({
                        position: new Point((xDiff - 5), yDiff),
                        username: data.username,
                        is_moving: data.is_moving,
                        direction: data.direction,
                    });
                    cameraView.players[colour].renderable = true;
                } else {
                    cameraView.players[colour].renderable = false;
                }
            }
        }

        this.zCooldown.progress = data.kill_timer / data.kill_cooldown;
        this.xCooldown.progress = data.sprint_timer / data.sprint_cooldown;
        this.cCooldown.progress = data.ability_timer / data.ability_cooldown;

        // Set player name
        this.name.text = data.username;
        // Sprite width / 2
        this.name.x = this.x * 16 + 8 - (gameView.context.measureText(data.username).width / 4);
        this.name.y = this.y * 16 - this.name.fontSize;
    }

    setWalkingAnimation(direction, sprites) {
        this.walkAnimations[direction / 90] = new AnimatedSpriteTile(sprites);
    }

    setIdleAnimation(direction, sprites) {
        this.idleAnimations[direction / 90] = new AnimatedSpriteTile(sprites);
    }

    render(context) {
        let sprite = null;

        if (this.moving)
            sprite = this.walkAnimations[this.direction / 90];
        else
            sprite = this.idleAnimations[this.direction / 90];

        if (sprite === null) sprite = this.sprite;

        sprite.x = this.x * 16;
        sprite.y = this.y * 16;
        sprite.render(context);

        // Render item on top of players head
        if (this.item !== null) {
            this.item.x = this.x * 16;
            this.item.y = this.y * 16 - 11;
            this.item.render(context);
        }

        // Render name above player
        this.name.render(context);
    }
}

const view = new View(context); // Main wrapper view
const loadingView = new View(context);
const menuView = new View(context); // Main menu view
const gameView = new View(context); // Game view
gameView.renderable = false;
gameView.zoom = 3;
view.addChild(menuView);
view.addChild(gameView);
view.addChild(loadingView);

loadingView.renderable = true;
menuView.renderable = false;


const statsView = new View(context); // Informative stats view (fps etc)
const UIView = new View(context); // UI View in game

// Only turn this on if you are the camera class
const cameraView = new View(context); // Camera view for scout class
cameraView.renderable = false;
cameraView.zoom = 2.5;

const scoreView = new View(context); // view for scoreboard
const playerView = new View(context);

menuView.addChild(playerView);

gameView.addChild(UIView);
gameView.addChild(statsView);
gameView.addChild(scoreView);
UIView.addChild(cameraView);

const TILE_SIZE = 48;
const STATS_INTERVAL = 1000 / 10;
let socket = io("/hallway");

let game = new HallwayHunters();

async function loadImages(src, callback) {
    return new Promise((resolve, reject) => {
        let image = new Image();
        image.onload = () => {
            callback(image);
            resolve();
        };
        image.onerror = reject;
        image.src = src;
    });
}

setBackground = (image) => {menuView.background = image};
loadImages("/static/images/tiles/dungeon_sheet.png", splitTileset).then(() =>
loadImages("/static/images/tiles/background.png", setBackground).then(() => {
    initialize();
}));

socket.on("join", (data) => {
    console.log(`${data} joined the room.`);
});
let startTime;

setInterval(function () {
    startTime = Date.now();
    socket.emit('ping');
}, STATS_INTERVAL);


socket.on('pong', function () {
    game.stats.ping.put(Date.now() - startTime);
});

$('#messageform').submit(function (e) {
    e.preventDefault(); // prevents page reloading
    let m = $('#m');
    let data = {
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
    console.log(data);
    console.log(messages);
    messages.append($('<li class="chat-message-entry" style="color:red">').text("Error: " + data));
    document.getElementById("messages").lastChild.scrollIntoView();
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

function initializeBoard(board_size) {
    for (let x = 0; x < board_size; x++) {
        let list = [];
        for (let y = 0; y < board_size; y++) {
            let sprite = new SpriteTile(game.tiles["void"]);
            sprite.x = x * 16;
            sprite.y = y * 16;
            list.push(sprite);
            gameView.addObjects(sprite);
        }
        game.state.board.push(list);
    }
}

function updateBoardSprites(tiles) {
    tiles.forEach(obj => {
        let oldTile = game.state.board[obj.x][obj.y];
        oldTile.setImage(game.tiles[obj.tile.image])
    });
}

function updateRenderable(oldCenter, newCenter) {
    const w = gameView.width / gameView.zoom;
    const h = gameView.height / gameView.zoom;
    const coordScale = 16;
    const oldRenderbox = new Rectangle(oldCenter.x - w / 2 - coordScale, oldCenter.y - h / 2 - coordScale, w + 32, h + 32);
    const newRenderbox = new Rectangle(newCenter.x - w / 2 - coordScale, newCenter.y - h / 2 - coordScale, w + 32, h + 32);

    [oldRenderbox, newRenderbox].forEach(e => {
        e.x = Math.max(Math.floor(e.x / coordScale), 0);
        e.y = Math.max(Math.floor(e.y / coordScale), 0);
        e.width = Math.ceil(e.width / coordScale);
        e.height = Math.ceil(e.height / coordScale);
    });

    // Remove the renderable property from the old box
    let width = Math.min(oldRenderbox.x + oldRenderbox.width, game.state.board_size);
    let height = Math.min(oldRenderbox.y + oldRenderbox.height, game.state.board_size);
    for (let x = oldRenderbox.x; x < width; x++) {
        for (let y = oldRenderbox.y; y < height; y++) {
            game.state.board[x][y].renderable = false;
        }
    }
    // Add the renderable property to the new box
    width = Math.min(newRenderbox.x + newRenderbox.width, game.state.board_size);
    height = Math.min(newRenderbox.y + newRenderbox.height, game.state.board_size);

    // TODO: Dont recompute the entire vision lines every new data update
    gameView.clearLayer(2);
    for (let x = newRenderbox.x; x < width; x++) {
        for (let y = newRenderbox.y; y < height; y++) {
            game.state.board[x][y].renderable = true;

            if (game.lookup[x] === undefined || !game.lookup[x][y]) {
                let tile = new ColorTile("rgba(0,0,0,0.2)");
                tile.x = x * 16;
                tile.y = y * 16;
                tile.z = 2;
                tile.renderable = true;

                gameView.addObjects(tile);
            }
        }
    }
}

function updateItems(tiles) {
    tiles.forEach(tile => {
        if (game.state.board[tile.x][tile.y].item !== undefined) {
            if (tile.tile.item === null) {
                // TODO: Remove this object from the renderable list
                game.state.board[tile.x][tile.y].item.renderable = false;
                game.state.board[tile.x][tile.y].item = undefined;
            } else {
                game.state.board[tile.x][tile.y].item.setImage(game.tiles[tile.tile.item.name]);
            }
            return;
        }
        if (tile.tile.item !== null) {
            let item = new SpriteTile(game.tiles[tile.tile.item.name]);
            // FIXME: Items aren't always renderable, update this.
            item.renderable = true;
            item.x = tile.x * 16;
            item.y = tile.y * 16;
            item.z = 1;
            game.state.board[tile.x][tile.y].item = item;
            gameView.addObjects(item);
        }
    });
}


function HallwayHunters() {
    this.state = {
        board_size: 30,
        all_players: [],
        visible_players: [],
        player_data: {
            dead: false,
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
            movement_cooldown: 0,
            movement_timer: 0,
            ability_cooldown: 0,
            ability_timer: 0,
            sprint_cooldown: 0,
            sprint_timer: 0,
            kill_cooldown: 0,
            kill_timer: 0,
            stored_items: [{
                name: "",
            }],
            passives: [{
                name: "",
                time: 0,
                total_time: 0
            }],
            camera_list: []
        },
        visible_tiles: [
            {x: 0, y: 0, tile: {}}
        ],
        board: [],

    };
    this.stats = {
        ping: new RollingAverage(5),
        stateTime: new RollingAverage(5),
        fps: new RollingAverage(5),
        frameTime: new RollingAverage(5)
    };
    this.statsText = {
        ping: new DrawableText(5, 5),
        fps: new DrawableText(5, 5 + 12),
        stateTime: new DrawableText(5, 5 + 24),
        frameTime: new DrawableText(5, 5 + 36),
    };
    this.lookup = {};
    this.tiles = {};
    this.items = [];

    this.players = {};

    this.setState = function (data) {
        let start = performance.now();
        if (this.state.board.length === 0) {
            initializeBoard(data.board_size);
        }

        if (data.visible_tiles !== undefined) {
            updateBoardSprites(data.visible_tiles);
            updateItems(data.visible_tiles);
        }

        this.state = {
            ...this.state,
            ...data
        };
        // This marks the tiles which are visible
        this.lookup = {};
        this.state.visible_tiles.forEach((obj) => {
            if (this.lookup[obj.x] === undefined) {
                this.lookup[obj.x] = {};
            }
            this.lookup[obj.x][obj.y] = true;
        });

        // Fix renderable players like this.
        for (const player of Object.values(this.players)) {
            player.renderable = false;
        }
        data.visible_players.forEach(player => {
            this.players[player.name].renderable = true;
            this.players[player.name].update(player);
        });


        this.state.all_players.forEach(player => {
            const p = this.players[player.name];
            p.score = player.stored_items.length;
            p.scoreText.text = player.username + " " + player.stored_items.length
        });

        let newCameraCenter = new Point(data.player_data.position.x * 16, data.player_data.position.y * 16);
        player.update(data.player_data);

        if (this.state.started)
            updateRenderable(gameView.cameraCenter, newCameraCenter);

        gameView.cameraCenter = newCameraCenter;

        this.stats.stateTime.put(performance.now() - start);
    };
}


function round(number) {
    return Math.round(number * 100) / 100;
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
}

// Game rendering stuff
let then = 0;

function gameLoop() {
    requestAnimationFrame(gameLoop);
    handleInput();

    const now = performance.now();
    const elapsed = now - then;

    // if enough time has elapsed, draw the next frame

    if (elapsed > FPS_INTERVAL) {
        // Get ready for next frame by setting then=now, but also adjust for your
        // specified fpsInterval not being a multiple of RAF's interval (16.7ms)
        then = now - (elapsed % FPS_INTERVAL);

        // Resizing the canvas should overwrite the width and height variables
        // It has to be a multiple of 2 to remove artifacts around the tilesets
        canvas.width = Math.round(canvas.clientWidth / 2) * 2;
        canvas.height = Math.round(canvas.clientHeight / 2) * 2;

        if (canvas.width !== gameView.width || canvas.height !== gameView.height) {
            gameView.width = canvas.width;
            gameView.height = canvas.height;

            // Its just works
            cameraView.cameraCenter.x = ((cameraView.width / 2) - canvas.width) / cameraView.zoom;
            cameraView.cameraCenter.y = (cameraView.height / 2) / cameraView.zoom;
        }

        // Clear the canvas and fill with floor tile color.
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(game.tiles["floor"], 0, 0, canvas.width, canvas.height);

        game.stats.fps.put(gameView.fps);
        game.stats.frameTime.put(gameView.frametime);

        game.statsText.fps.text = round(game.stats.fps.get()) + " fps";
        game.statsText.stateTime.text = "State update time: " + round(game.stats.stateTime.get()) + " ms";
        game.statsText.ping.text = "Latency: " + round(game.stats.ping.get()) + " ms";
        game.statsText.frameTime.text = "Frame time: " + round(game.stats.frameTime.get()) + " ms";

        // Compute the offset for all tiles, to center rendering on the player.
        try {
            view.render();
        } catch (e) {
            console.log(e);
        }
    }

}


function splitTileset(tileSet) {
    const scale = TILE_SIZE / 16;
    let canvas = document.createElement("canvas");
    canvas.className = "disable-anti-aliasing";
    canvas.width = tileSet.width * scale;
    canvas.height = tileSet.height * scale;
    let context = canvas.getContext("2d");

    context.clearRect(0, 0, canvas.width, canvas.height);
    context.webkitImageSmoothingEnabled = false;
    context.mozImageSmoothingEnabled = false;
    context.imageSmoothingEnabled = false;

    context.scale(scale, scale);
    context.drawImage(tileSet, 0, 0);

    const S = TILE_SIZE;

    game.tiles["edge_b"] = context.getImageData(6 * S, S, S, S);
    game.tiles["edge_b_top"] = context.getImageData(6 * S, 0, S, S);
    game.tiles["edge_b_alt1"] = context.getImageData(8 * S, 5 * S, S, S);
    game.tiles["edge_b_alt1_top"] = context.getImageData(8 * S, 4 * S, S, S);
    game.tiles["edge_b_alt2"] = context.getImageData(9 * S, 5 * S, S, S);
    game.tiles["edge_b_alt2_top"] = context.getImageData(9 * S, 4 * S, S, S);
    game.tiles["edge_b_alt3"] = context.getImageData(5 * S, 4 * S, S, S);

    game.tiles["corner_br"] = context.getImageData(9 * S, 3 * S, S, S);
    game.tiles["corner_br_top"] = context.getImageData(9 * S, 2 * S, S, S);

    game.tiles["corner_bl"] = context.getImageData(8 * S, 3 * S, S, S);
    game.tiles["corner_bl_top"] = context.getImageData(8 * S, 2 * S, S, S);

    game.tiles["corner_tr"] = context.getImageData(9 * S, S, S, S);
    game.tiles["corner_tr_top"] = context.getImageData(9 * S, 0, S, S);

    game.tiles["corner_tl"] = context.getImageData(8 * S, S, S, S);
    game.tiles["corner_tl_top"] = context.getImageData(8 * S, 0, S, S);

    game.tiles["inner_corner_br"] = context.getImageData(7 * S, 3 * S, S, S);
    game.tiles["inner_corner_br_top"] = context.getImageData(7 * S, 2 * S, S, S);

    game.tiles["inner_corner_bl"] = context.getImageData(5 * S, 3 * S, S, S);
    game.tiles["inner_corner_bl_top"] = context.getImageData(5 * S, 2 * S, S, S);

    game.tiles["inner_corner_tr"] = context.getImageData(7 * S, S, S, S);
    game.tiles["inner_corner_tr_top"] = context.getImageData(7 * S, 0, S, S);

    game.tiles["inner_corner_tl"] = context.getImageData(5 * S, S, S, S);
    game.tiles["inner_corner_tl_top"] = context.getImageData(5 * S, 0, S, S);

    game.tiles["edge_t"] = context.getImageData(6 * S, 3 * S, S, S);
    game.tiles["edge_t_alt1"] = context.getImageData(7 * S, 5 * S, S, S);

    game.tiles["edge_l"] = context.getImageData(7 * S, 2 * S, S, S);
    game.tiles["edge_l_alt1"] = context.getImageData(6 * S, 4 * S, S, S);
    game.tiles["edge_l_alt2"] = context.getImageData(7 * S, 4 * S, S, S);

    game.tiles["edge_r"] = context.getImageData(5 * S, 2 * S, S, S);
    game.tiles["void"] = context.getImageData(S, S, S, S);
    game.tiles["edge_t"] = context.getImageData(6 * S, 3 * S, S, S);

    game.tiles["floor"] = context.getImageData(6 * S, 2 * S, S, S);
    game.tiles["wall_test"] = context.getImageData(6 * S, S, S, S);

    game.tiles["door"] = context.getImageData(7 * S, 7 * S, S, S);
    game.tiles["ladder"] = context.getImageData(15 * S, 8 * S, S, S);
    game.tiles["camera"] = context.getImageData(7 * S, 6 * S, S, S);

    game.tiles["UI_corner_bl"] = context.getImageData(19 * S, 11 * S, S, S);
    game.tiles["UI_edge_left"] = context.getImageData(20 * S, 11 * S, S, S);
    game.tiles["UI_edge_bottom"] = context.getImageData(21 * S, 11 * S, S, S);

    ["red", "blue", "green", "purple", "black"].map((color, row) => {
        for (let i = 0; i < 3; i++) {
            game.tiles[color + "_90_" + i] = context.getImageData(i * S, (11 + row) * S, S, S);
            game.tiles[color + "_270_" + i] = context.getImageData((i + 3) * S, (11 + row) * S, S, S);
            game.tiles[color + "_180_" + i] = context.getImageData((i + 6) * S, (11 + row) * S, S, S);
            game.tiles[color + "_0_" + i] = context.getImageData((i + 9) * S, (11 + row) * S, S, S);
        }
        game.tiles[color + "_dead"] = context.getImageData(12 * S, (11 + row) * S, S, S);

        // Base chest sprite without animation
        game.tiles["chest_" + color] = context.getImageData(13 * S, (11 + row) * S, S, S);
        for (let i = 0; i < 6; i++) {
            game.tiles["chest_" + color + "_" + i] = context.getImageData((i + 13) * S, (11 + row) * S, S, S);
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

    console.log("Done loading images.");
}

/*
 * This function should get called when the game has started, and we know how many player entities need to be rendered
 */
function initializePlayers(dictionary) {
    const colours = ["red", "blue", "green", "purple", "black"];
    colours.forEach(colour => {
        let player = new Player(game.tiles[`${colour}_0_0`]);
        [0, 90, 180, 270].forEach(d => {
            player.setWalkingAnimation(d, [
                game.tiles[`${colour}_${d}_0`],
                game.tiles[`${colour}_${d}_1`],
                game.tiles[`${colour}_${d}_0`],
                game.tiles[`${colour}_${d}_2`],
            ]);

            player.setIdleAnimation(d, [
                game.tiles[`${colour}_${d}_0`]
            ]);
        });
        dictionary[colour] = player;
    });
}


let player = null;

function initializeCamera() {
    const camWidth = 5;
    if (player.cameraTiles === null) {
        // Only do this once
        let tile = new SpriteTile(game.tiles["UI_corner_bl"]);
        tile.renderable = true;
        tile.x = -5 * 16;
        tile.y = 4 * 16;
        tile.z = 3;
        cameraView.addObjects(tile);
        for (let i = 0; i < camWidth - 1; i++) {
            // Render left border
            tile = new SpriteTile(game.tiles["UI_edge_left"]);
            tile.renderable = true;
            tile.x = -5 * 16;
            tile.y = i * 16;
            tile.z = 3;
            cameraView.addObjects(tile);

            // Render bottom border
            tile = new SpriteTile(game.tiles["UI_edge_bottom"]);
            tile.renderable = true;
            tile.x = (i - 4) * 16;
            tile.y = 4 * 16;
            tile.z = 3;
            cameraView.addObjects(tile);
        }
        tile = new SpriteTile(game.tiles["floor"]);
        tile.renderable = true;
        tile.x = -camWidth * 16;
        tile.y = 0;
        tile.z = 0;
        tile.width = camWidth * 16;
        tile.height = camWidth * 16;
        cameraView.addObjects(tile);
    } else {
        // Cleanup existing objects, its O(n^2)..
        player.cameraTiles.forEach(e => {
            cameraView.removeObject(e, 0);
        });
    }

    player.cameraTiles = [];
    for (let i = 0; i < camWidth; i++) {
        for (let j = 0; j < camWidth; j++) {
            const tile = new SpriteTile(game.tiles["void"]);
            tile.renderable = true;
            tile.x = (i - 5) * 16;
            tile.y = j * 16;
            // Create an item but make it not-renderable.
            tile.item = new SpriteTile(game.tiles["void"]);
            tile.item.x = tile.x;
            tile.item.y = tile.y;

            cameraView.addObjects(tile);
            cameraView.addObjects(tile.item);
            player.cameraTiles.push(tile);
        }
    }

}


function initializeMenu() {
    const x = canvas.clientWidth / 2;

    const buttonWidth = 200;
    const buttonHeight = 50;
    const button = new Button(x - buttonWidth / 2, 600 - buttonHeight / 2, buttonWidth, buttonHeight);
    button.hoverColor = "#5f7791";
    button.color = "#3c5978";
    button.setOnClick(canvas, () => {
        socket.emit("start", {
            room: ROOM_ID
        });
    });
    button.renderable = true;

    const buttonText = new DrawableText(x, 600);
    buttonText.text = "Start";
    buttonText.fontSize = 25;
    buttonText.color = "rgb(207,226,255)";
    buttonText.centered = true;
    buttonText.z = 1;

    const title = new DrawableText(x, 100);
    title.text = "Hallway Hunters";
    title.fontSize = 45;
    title.color = "rgb(207,226,255)";
    title.borderColor = "#131c2c";
    title.centered = true;

    let classButtons = [];
    PLAYER_CLASSES.map((tuple, i) => {
        let cls = tuple[0];
        let info = tuple[1];

        let blockPadding = 20;
        let blockSize = 80;
        const offset = (PLAYER_CLASSES.length * (blockSize + blockPadding) - blockPadding) / 2 - (blockSize + blockPadding) * i;
        const button = new Button(x - offset, 200, blockSize, blockSize);
        button.hoverColor = "#5f7791";
        button.color = "#3c5978";
        const text = new DrawableText(button.x + blockSize / 2, button.y + blockSize / 2);
        text.color = "rgb(207,226,255)";
        text.text = cls;
        text.centered = true;

        const infoText = new DrawableText(x, button.y + 100);
        infoText.color = "rgb(207,226,255)";
        infoText.fontSize = 18;
        infoText.text = info;
        infoText.centered = true;
        infoText.renderable = false;
        button.infoText = infoText;

        classButtons.push(button);
        menuView.addObjects(button, text, infoText);
    });

    classButtons.forEach(clsButton => {
        clsButton.setOnClick(canvas, () => {
            classButtons.forEach(button => {
                button.color = "#3c5978";
                button.infoText.renderable = false;
            });
            clsButton.color = "#5f7791";
            clsButton.infoText.renderable = true;
        });
    });

    // playerView.addObjects()

    let background = new SpriteTile(menuView.background);
    background.width = menuView.background.width;
    background.height = menuView.background.height;
    background.renderable = true;
    let overlay = new ColorTile("#55555555");
    overlay.width = background.width;
    overlay.height = background.height;
    overlay.renderable = true;
    background.z = overlay.z = -1;

    menuView.addObjects(background, overlay, buttonText, button, title);
}

function initializeLoading() {
    let background = new SpriteTile(menuView.background);
    background.renderable = true;
    background.width = menuView.background.width;
    background.height = menuView.background.height;
    let overlay = new ColorTile("#55555555");
    overlay.renderable = true;
    overlay.width = background.width;
    overlay.height = background.height;
    background.z = overlay.z = -1;

    class CircleLoading extends Point {
        constructor(x, y, radius) {
            super(x, y);
            this.renderable = true;
            this.z = 2;
            this.radius = radius;
            this.tick = 0;
            this.chasing = true;
            this.ticksPerRotation = 180;
            this.chaseSpeed = 2.4;
        }
        render(context) {
            const phi = (2 * Math.PI);
            this.tick++;

            if (this.tick % (this.ticksPerRotation / this.chaseSpeed) === 1) this.chasing = !this.chasing;

            const a1 = (this.tick % this.ticksPerRotation) / this.ticksPerRotation * phi;
            const a2 = (a1 + ((this.tick * this.chaseSpeed) % this.ticksPerRotation) / this.ticksPerRotation * phi) % (phi);

            console.log(a1, a2);
            let sAngle, eAngle;
            if (this.chasing) {
                sAngle = a1; eAngle = a2;
            } else {
                sAngle = a2; eAngle = a1;
            }
            context.lineWidth = 15;
            context.strokeStyle = this.mainColour;
            context.beginPath();
            context.arc(this.x, this.y, this.radius, sAngle, eAngle);
            context.stroke();
        }
    }

    const circleLoading = new CircleLoading(background.width/2,  background.height/2, 35);

    loadingView.addObjects(background, overlay, circleLoading);
}


function updateScoreboard() {
    scoreView.clearLayer(0);
    let sorted_score = [];
    Object.values(game.players).forEach(player => {
        sorted_score.push([player, player.score])
    });

    sorted_score.sort(function(a, b) {
        return a[1] - b[1];
    });

    sorted_score.map((player, i) => {
        player[0].scoreText.x = canvas.width - 100;
        player[0].scoreText.y = canvas.height - i * player[0].scoreText.fontSize - 50;
        scoreView.addObjects(player[0].scoreText);
    })
}

function postStartInitialize(data) {
    player = game.players[data.player_data.name];

    // Setup UI cooldowns
    UIView.addObjects(player.zCooldown);
    UIView.addObjects(player.xCooldown);
    UIView.addObjects(player.cCooldown);

    updateScoreboard();
    // Setup camera
    initializeCamera();
}

let intervalID;

function initialize() {
    intervalID = requestAnimationFrame(gameLoop);
    initializeLoading();

    initializeMenu();
    initializePlayers(game.players);
    // Store player objects in the cameraView.
    cameraView.players = {};
    initializePlayers(cameraView.players);
    for (let key in game.players) {
        if (game.players.hasOwnProperty(key)) {
            game.players[key].renderable = true;
            game.players[key].z = 3;
            gameView.addObjects(game.players[key]);

            cameraView.players[key].z = 2;
            cameraView.addObjects(cameraView.players[key])
        }
    }

    // Setup stats view
    statsView.addObjects(
        game.statsText.frameTime,
        game.statsText.fps,
        game.statsText.ping,
        game.statsText.stateTime
    );


    // cameraView.renderable = true;

    /*
     * Register all socket.io functions to the game object.
     */
    socket.on("game_state", (data) => {
        if (player === null) {
            postStartInitialize(data);
        }
        game.setState(data);
        if (game.state.started) {
            updateScoreboard();
        }

    });
    socket.on("message", (data) => {
        console.log(data);
    });

    // Request game state on initialization.
    socket.emit("game_state", {
        "room": ROOM_ID
    });

    loadingView.renderable = false;
    menuView.renderable = true;
}

function sendAction(action) {
    let data = {
        room: ROOM_ID,
        action: action
    };
    socket.emit("action", data);
}

socket.on("loading", () => {
    menuView.renderable = false;
    loadingView.renderable = true;
});

socket.on("start", () => {
    loadingView.renderable = false;
    gameView.renderable = true;
});

function toggleReady() {
    const cls = document.getElementById("class-selector").value;
    socket.emit("start", {
        room: ROOM_ID,
        player_class: cls,
    });
};

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
    // TODO: Refactor this to not be dumb (maybe get valid actions from server?)
    if (ev.key === "c" ||
        ev.key === "x" ||
        ev.key === "z" ||
        ev.key === "Shift") {
        sendAction(ev.key);
    }
});
document.addEventListener("keyup", (ev) => {
    keyState[ev.key] = false;
    sendMove({x: 0, y: 0});
});

socket.emit("join", {
    "room": ROOM_ID,
});
