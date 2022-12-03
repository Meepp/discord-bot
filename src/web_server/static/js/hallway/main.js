import {
    Button,
    DrawableText,
    View,
    round,
    SpriteTile,
    ColorTile,
    Point,
} from "../engine/engine.js";
import {getUsername} from "../engine/auth.js";
import {HallwayHunters} from "./hallway.js";
import {COLORS, loadImages, TileSet} from "./resources.js";

let canvas = document.getElementById("canvas");
let context = canvas.getContext("2d");
context.webkitImageSmoothingEnabled = false;
context.mozImageSmoothingEnabled = false;
context.imageSmoothingEnabled = false;

const FPS_INTERVAL = 1000 / 60;

let game;

const view = new View(context); // Main wrapper view
view.width = canvas.width;
view.height = canvas.height;
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
const UIView = new View(context); // UI View in game, docked at the bottom
const scoreView = new View(context); // view for scoreboard

gameView.addChild(UIView);
gameView.addChild(statsView);
gameView.addChild(scoreView);

const TILE_SIZE = 48;
const STATS_INTERVAL = 1000 / 10;
let socket = io("/hallway");


function loadMainContent(gameWrapper) {
    let divs = document.getElementsByClassName("main-content");
    Array.from(divs).forEach((div) => {
        div.style.display = "none";
    });

    document.getElementById(gameWrapper).style.display = "flex";
}


// Game rendering stuff
let then = 0;

function gameLoop() {
    requestAnimationFrame(gameLoop);

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
        }

        // Clear the canvas and fill with floor tile color.
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(game.tileSet.tiles["floor"], 0, 0, canvas.width, canvas.height);

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

    let blockSize = 80;
    let classButtons = [];
    PLAYER_CLASSES.map((tuple, i) => {
        let cls = tuple[0];
        let info = tuple[1];

        let blockPadding = 20;
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

    let background = new SpriteTile(menuView.background);
    background.width = menuView.background.width;
    background.height = menuView.background.height;
    background.renderable = true;
    let overlay = new ColorTile("#55555555");
    overlay.width = background.width;
    overlay.height = background.height;
    overlay.renderable = true;
    background.z = overlay.z = -1;

    menuView.colorButtons = {};
    COLORS.map((color, i) => {
        let button = new Button(50, 200 + i * 100, blockSize, blockSize);
        button.hoverColor = "#5f7791";
        button.color = "#3c5978";
        button.text = new DrawableText(button.x + blockSize / 2, button.y + blockSize / 2);
        button.text.color = color;
        button.text.text = color;
        button.text.fontSize = 15;
        button.text.centered = true;
        button.playerText = new DrawableText(button.x + blockSize + 10, button.y + blockSize / 2);
        button.playerText.fontSize = 20;
        button.playerText.color = "#fff";
        menuView.colorButtons[color] = button;
        button.setOnClick(canvas, (_) => {
            socket.emit("changeColor", {
                room_id: ROOM_ID,
                color: color,
            });
        });
        menuView.addObjects(button, button.text, button.playerText);
    });


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

            if (this.tick % (this.ticksPerRotation / this.chaseSpeed) === 0) this.chasing = !this.chasing;

            const a1 = (this.tick % this.ticksPerRotation) / this.ticksPerRotation * phi;
            const a2 = (a1 + ((this.tick * this.chaseSpeed) % this.ticksPerRotation) / this.ticksPerRotation * phi) % (phi);

            let sAngle, eAngle;
            if (this.chasing) {
                sAngle = a1;
                eAngle = a2;
            } else {
                sAngle = a2;
                eAngle = a1;
            }
            context.lineWidth = 15;
            context.strokeStyle = this.mainColour;
            context.beginPath();
            context.arc(this.x, this.y, this.radius, sAngle, eAngle);
            context.stroke();
        }
    }

    const circleLoading = new CircleLoading(background.width / 2, background.height / 2, 35);
    loadingView.infoText = new DrawableText(background.width / 2, background.height / 2 + 100);
    loadingView.infoText.color = "#ffffff";
    loadingView.infoText.fontSize = 20;
    loadingView.infoText.centered = true;
    loadingView.addObjects(background, overlay, circleLoading, loadingView.infoText);
}


function updateScoreboard() {
    scoreView.clearLayer(0);
    let sorted_score = [];
    Object.values(game.players).forEach(player => {
        sorted_score.push([player, player.score])
    });

    sorted_score.sort(function (a, b) {
        return a[1] - b[1];
    });

    sorted_score.map((player, i) => {
        player[0].scoreText.x = canvas.width - 100;
        player[0].scoreText.y = canvas.height - i * player[0].scoreText.fontSize - 50;
        scoreView.addObjects(player[0].scoreText);
    })
}

function postStartInitialize(data) {
    updateScoreboard();
}

let intervalID;
let started = false;

function start() {
    intervalID = requestAnimationFrame(gameLoop);
    initializeLoading();

    initializeMenu();
    game.initializePlayers();
    game.initializeCards();

    // Initialize player sprites
    for (let key in game.players) {
        if (game.players.hasOwnProperty(key)) {
            game.players[key].renderable = true;
            game.players[key].z = 3;
            gameView.addObjects(game.players[key]);
        }
    }

    // Setup stats view
    statsView.addObjects(
        game.statsText.frameTime,
        game.statsText.fps,
        game.statsText.ping,
        game.statsText.stateTime
    );


    /*
     * Register all socket.io functions to the game object.
     */
    socket.on("game_state", (data) => {
        if (!data.started) {
            // Lobby information
            COLORS.forEach(color => {
                menuView.colorButtons[color].playerText.text = ""
            });
            data.all_players.forEach(player => {
                menuView.colorButtons[player.color].playerText.text = player.username;
            });
        } else {
            game.setState(data);

            if (!started) {
                postStartInitialize(data);
                started = true;
            }
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

function initialize() {
    let tileSet = new TileSet();

    let setBackground = (image) => {
        menuView.background = image
    };

    loadImages("/static/images/tiles/dungeon_sheet.png", (x) => tileSet.splitTileset(x)).then(() =>
        loadImages("/static/images/tiles/background.png", setBackground).then(() => {
            start();
        }));
    game = new HallwayHunters(gameView, UIView, tileSet);

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

    // Keylisteners for user input
    document.addEventListener("keydown", (ev) => {
        const VALID_ACTIONS = [
           "1", "2", "3", "4", "5", "6", "7", "8", "Enter", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"
        ];
        if (VALID_ACTIONS.indexOf(ev.key) !== -1) {
            sendAction(ev.key);
        }
    });

    // Emit join event for server to register user
    socket.emit("join", {
        "room": ROOM_ID,
    });
}

function sendAction(action) {
    let data = {
        room: ROOM_ID,
        action: action
    };
    socket.emit("action", data);
}

socket.on("loading", (data) => {
    loadingView.infoText.text = data;
    menuView.renderable = false;
    loadingView.renderable = true;
});

socket.on("start", () => {
    loadingView.renderable = false;
    gameView.renderable = true;
});


function changeSettings() {
    let data = {
        room_id: ROOM_ID,
        settings: {}
    };
    socket.emit("change settings", data)
}


socket.on("set_session", (data) => {
    USER_NAME = data;
    initialize();
});

// Start the game
socket.emit("set_session", {username: getUsername()});


