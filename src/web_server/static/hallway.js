let canvas = document.getElementById("canvas");
let context = canvas.getContext("2d");
context.webkitImageSmoothingEnabled = false;
context.mozImageSmoothingEnabled = false;
context.imageSmoothingEnabled = false;


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

        // Only useful when you are the scout
        this.cameraTiles = null;

        const padding = 10;
        const radius = 30;
        this.zCooldown = new CircularCooldown(padding + radius * 2, view.height - padding, radius);
        this.zCooldown.textObject.text = "Z";
        this.xCooldown = new CircularCooldown(padding + radius * 5, view.height - padding, radius);
        this.xCooldown.textObject.text = "X";
        this.cCooldown = new CircularCooldown(padding + radius * 8, view.height - padding, radius);
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
        player.x = data.position.x;
        player.y = data.position.y;
        player.moving = data.is_moving;
        player.direction = data.direction;

        if (data.item !== null)
            this.item = new SpriteTile(game.tiles[data.item.name]);
        else
            this.item = null;

        for (let i = 0; i < data.camera_list.length; i++) {
            let tile = game.tiles[data.camera_list[i].image];
            player.cameraTiles[i].setImage(tile)
        }


        this.zCooldown.progress = data.kill_timer / data.kill_cooldown;
        this.xCooldown.progress = data.sprint_timer / data.sprint_cooldown;
        this.cCooldown.progress = data.ability_timer / data.ability_cooldown;
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
    }
}

const view = new View(context);
const statsView = new View(context);
const UIView = new View(context);

// Only turn this on if you are the camera class
const cameraView = new View(context);
cameraView.renderable = false;
cameraView.zoom = 2.5;

view.addChild(UIView);
view.addChild(statsView);
UIView.addChild(cameraView);

view.zoom = 3;
const TILE_SIZE = 48;
const STATS_INTERVAL = 1000 / 10;

const FRAMES_PER_ANIMATION = 6;
let socket = io("/hallway");
let tileSet;

let game = new HallwayHunters();

async function loadImages(src) {
    return new Promise((resolve, reject) => {
        tileSet = new Image();
        tileSet.onload = () => {
            splitTileset(tileSet.width, tileSet.height);
            resolve();
        };
        tileSet.onerror = reject;
        tileSet.src = src;
    });
}


loadImages("/static/images/tiles/dungeon_sheet.png").then(e => {
        initialize();
    }
);

socket.on("join", (data) => {
    console.log(`${data} joined the room.`);
});
let startTime;

setInterval(function() {
    startTime = Date.now();
    socket.emit('ping');
}, STATS_INTERVAL);


socket.on('pong', function() {
    game.stats.ping.put(Date.now() - startTime);
});

$('#messageform').submit(function(e) {
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

function getRelativeMousePosition(canvas, evt) {
    let rect = canvas.getBoundingClientRect();
    return {
        x: evt.clientX - rect.left,
        y: evt.clientY - rect.top
    };
}

function initializeBoard(board_size) {
    for (let x = 0; x < board_size; x++) {
        let list = [];
        for (let y = 0; y < board_size; y++) {
            let sprite = new SpriteTile(game.tiles["void"]);
            sprite.x = x * 16;
            sprite.y = y * 16;
            list.push(sprite);
            view.objects[0].push(sprite);
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
    const w = view.width / view.zoom;
    const h = view.height / view.zoom;
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
    view.objects[2] = [];
    for (let x = newRenderbox.x; x < width; x++) {
        for (let y = newRenderbox.y; y < height; y++) {
            game.state.board[x][y].renderable = true;

            if (game.lookup[x] === undefined || !game.lookup[x][y]) {
                let tile = new ColorTile("rgba(0,0,0,0.2)");
                tile.x = x * 16;
                tile.y = y * 16;
                tile.renderable = true;
                view.objects[2].push(tile);
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
            game.state.board[tile.x][tile.y].item = item;
            view.objects[1].push(item);
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
            camera_list: [],
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
    this.animations = {};
    this.items = [];
    this.playerText = new DrawableText(0, 0);

    this.setState = function(data) {
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

        let newCameraCenter = new Point(data.player_data.position.x * 16, data.player_data.position.y * 16);
        player.update(data.player_data);

        this.playerText.text = data.player_data.username;
        // Sprite width / 2
        this.playerText.x = player.x * 16 + 8 - (view.context.measureText(data.player_data.username).width / 4);
        this.playerText.y = player.y * 16 - this.playerText.fontSize;

        if (this.state.started)
            updateRenderable(view.cameraCenter, newCameraCenter);

        view.cameraCenter = newCameraCenter;

        this.stats.stateTime.put(performance.now() - start);
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

            // if (game.state.player_data.objective.x === x && game.state.player_data.objective.y === y) {
            //     context.fillStyle = "#63ee52";
            // }

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
    const x = canvas.width - 100;
    const y = canvas.height - 100;

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
    const x = player.position.x * S + xOffset;
    const y = player.position.y * S + yOffset;

    let sprite;
    if (player.dead) {
        sprite = game.tiles[player.name + "_dead"];
    } else {
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
        sprite = getAnimationFrame(animation);
    }

    context.drawImage(sprite, x, y);
    if (player.item !== null) {
        context.drawImage(game.tiles[player.item.name], x, y - S / 2 - 7);
    }
}

function renderStorage() {
    const padding = 10;
    const S = TILE_SIZE;
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
function gameLoop() {
    handleInput();

    // Resizing the canvas should overwrite the width and height variables
    // It has to be a multiple of 2 to remove artifacts around the tilesets
    canvas.width = Math.round(canvas.clientWidth / 2) * 2;
    canvas.height = Math.round(canvas.clientHeight / 2) * 2;

    if (canvas.width !== view.width || canvas.height !== view.height) {
        view.width = canvas.width;
        view.height = canvas.height;

        // Its just works
        cameraView.cameraCenter.x = ((cameraView.width / 2) - view.width) / cameraView.zoom;
        cameraView.cameraCenter.y = (cameraView.height / 2) / cameraView.zoom;
    }

    // Clear the canvas and fill with floor tile color.
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.drawImage(game.tiles["floor"], 0, 0, canvas.width, canvas.height);

    game.stats.fps.put(view.fps);
    game.stats.frameTime.put(view.frametime);

    game.statsText.fps.text = round(game.stats.fps.get()) + " fps";
    game.statsText.stateTime.text = "State update time: " + round(game.stats.stateTime.get()) + " ms";
    game.statsText.ping.text = "Latency: " + round(game.stats.ping.get()) + " ms";
    game.statsText.frameTime.text = "Frame time: " + round(game.stats.frameTime.get()) + " ms";

    // Compute the offset for all tiles, to center rendering on the player.
    try {
        view.render();
    } catch (e) {
        console.log(e);
        clearInterval(intervalID);
    }
}

function createAnimation(sprites) {
    return {
        sprites: sprites,
        frameNumber: 0,
        currentSprite: 0,
        active: false,
        finishAnimation: false,
    };
}

function splitTileset(width, height) {
    const scale = TILE_SIZE / 16;
    let canvas = document.createElement("canvas");
    canvas.className = "disable-anti-aliasing";
    canvas.width = width * scale;
    canvas.height = height * scale;
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

    console.log("Done loading images.");
}

let player;

function initializeCamera() {
    player.cameraTiles = [];
    const camWidth = 5;
    for (let i = 0; i < camWidth; i++) {
        for (let j = 0; j < camWidth; j++) {
            const tile = new SpriteTile(game.tiles["void"]);
            tile.renderable = true;
            tile.x = (i - 5) * 16;
            tile.y = j * 16;
            cameraView.objects[0].push(tile);
            player.cameraTiles.push(tile);
        }
    }

    let tile = new SpriteTile(game.tiles["UI_corner_bl"]);
    tile.renderable = true;
    tile.x = -5 * 16;
    tile.y = 4 * 16;
    cameraView.objects[1].push(tile);
    for (let i = 0; i < camWidth - 1; i++) {
        // Render left border
        tile = new SpriteTile(game.tiles["UI_edge_left"]);
        tile.renderable = true;
        tile.x = -5 * 16;
        tile.y = i * 16;
        cameraView.objects[1].push(tile);

        // Render bottom border
        tile = new SpriteTile(game.tiles["UI_edge_bottom"]);
        tile.renderable = true;
        tile.x = (i - 4) * 16;
        tile.y = 4 * 16;
        cameraView.objects[1].push(tile);
    }
}

function initialize() {
    player = new Player(game.tiles["red_0_0"]);
    [0, 90, 180, 270].forEach(d => {
        player.setWalkingAnimation(d, [
            game.tiles[`red_${d}_0`],
            game.tiles[`red_${d}_1`],
            game.tiles[`red_${d}_0`],
            game.tiles[`red_${d}_2`],
        ]);

        player.setIdleAnimation(d, [
            game.tiles[`red_${d}_0`]
        ]);
    });
    view.objects[3].push(player);
    view.objects[3].push(game.playerText);
    game.playerText.fontSize = 6;
    game.playerText.color = "#000";

    UIView.objects[0].push(player.zCooldown);
    UIView.objects[0].push(player.xCooldown);
    UIView.objects[0].push(player.cCooldown);

    statsView.objects[0].push(
        game.statsText.frameTime,
        game.statsText.fps,
        game.statsText.ping,
        game.statsText.stateTime
    );

    initializeCamera();
    cameraView.renderable = true;

    /*
     * Register all socket.io functions to the game object.
     */
    socket.on("game_state", (data) => {
        game.setState(data);
        let list = !game.state.started ? $(".user-list") : $(".player-list")
        list.empty()
        if (!game.state.started) {
            // Lobby stuff
            data.all_players.forEach(player => {
                list.append(`
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
            data.all_players.forEach(player => {
                list.append(`
                    <div class="user-entry">
                    <div class="user-entry-name">${player.username}</div>
                    <div class="user-entry-name">${!player.dead ? "Alive" : "Dead"}</div>
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
let intervalID;
socket.on("start", () => {
    loadMainContent("game-wrapper");
    if (!has_started) {
        has_started = true;
        intervalID = setInterval(gameLoop, 1000 / 60);
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
