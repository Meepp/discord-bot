import {Button, DrawableText, RollingAverage, round, View} from "./engine.js";

let canvas = document.getElementById("canvas");
let context = canvas.getContext("2d");
context.webkitImageSmoothingEnabled = false;
context.mozImageSmoothingEnabled = false;
context.imageSmoothingEnabled = false;

const FPS_INTERVAL = 1000 / 60;

const view = new View(context); // Main wrapper view
view.width = canvas.width;
view.height = canvas.height;


const WORD_LENGTH = 5;
const MAX_GUESSES = 10;

class ColorTextTile extends DrawableText {
    constructor(x, y, color) {
        super(color);

        this.centered = true;
        this.x = x;
        this.y = y;

        this.fillColor = color;

        this.z = 0;
        this.renderable = true;
    }

    render(context) {
        context.fillStyle = this.fillColor;
        context.fillRect(this.x - this.width / 2, this.y - this.height / 2, this.width, this.height);
        super.render(context);
    }
}

class Colors {
    static UNGUESSED = "#999";
    static GUESSED = "#5f5f5f";
}

class Wordle {
    STATS_INTERVAL = 1000 / 10;
    SQUARE_SIZE = 48;
    PADDING = 4;

    tiles = new Array(MAX_GUESSES);
    guessBar = new Array(WORD_LENGTH);
    answerBar = new Array(WORD_LENGTH);

    menuView = new View(context); // Player menu view
    playerView = new View(context);
    gameView = new View(context); // Game view

    statsView = new View(context); // Informative stats view (fps etc)
    stats = {
        ping: new RollingAverage(5),
        stateTime: new RollingAverage(5),
        fps: new RollingAverage(5),
        frameTime: new RollingAverage(5)
    };
    statsText = {
        ping: new DrawableText(5, 5),
        fps: new DrawableText(5, 5 + 12),
        stateTime: new DrawableText(5, 5 + 24),
        frameTime: new DrawableText(5, 5 + 36),
    };
    displayPointerY = 0;
    textPointerX = 0;
    started = false;
    correct = false;
    endTime = new Date();
    clock = new DrawableText(0, 0);

    initialize(data) {
        console.log(data);
        this.endTime = new Date(data.end_time);
        this.textPointerX = 0;
        this.displayPointerY = 0;


        // Reset guess on game initialization.
        this.correct = false;

        this.started = true;
        this.gameView.addChild(this.statsView);
        this.gameView.cameraCenter.x = this.SQUARE_SIZE * WORD_LENGTH / 2;
        this.gameView.cameraCenter.y = this.SQUARE_SIZE * MAX_GUESSES / 2;
        this.gameView.renderable = true;

        this.clock.x = this.SQUARE_SIZE * WORD_LENGTH / 2;
        this.clock.y = -this.SQUARE_SIZE;
        this.clock.centered = true;
        this.clock.fontSize = this.SQUARE_SIZE * .8;
        this.clock.color = "black";
        this.gameView.addObjects(this.clock);

        this.menuView.addChild(this.playerView);
        this.menuView.renderable = true;
        this.playerView.renderable = true;

        for (let y = 0; y < MAX_GUESSES; y++) {
            this.tiles[y] = new Array(WORD_LENGTH);
            for (let x = 0; x < WORD_LENGTH; x++) {
                this.tiles[y][x] = this.tileGenerator(x, y, "");
            }
        }

        this.initializeBars();
        this.initializeQwerty();

        for (let y = 0; y < MAX_GUESSES; y++) {
            game.gameView.addObjects(...game.tiles[y])
        }
    }

    tileGenerator(x, y, text) {
        let tile = new ColorTextTile(x * (this.SQUARE_SIZE + this.PADDING), y * (this.SQUARE_SIZE + this.PADDING), Colors.UNGUESSED);
        tile.width = this.SQUARE_SIZE;
        tile.height = this.SQUARE_SIZE;
        tile.fontSize = this.SQUARE_SIZE * .8;
        tile.text = text;
        return tile;
    }

    initializeBars() {
        /*
        * Initialize guess bar in which to type, and the answer bar when the game is over.
        */
        for (let x = 0; x < WORD_LENGTH; x++) {
            // Place input bar under board tiles
            this.guessBar[x] = this.tileGenerator(x, MAX_GUESSES + 1, "");
            this.answerBar[x] = this.tileGenerator(x, -2, "");
        }

        console.log(this.guessBar, this.answerBar);

        this.gameView.addObjects(...this.guessBar);
        this.gameView.addObjects(...this.answerBar);
    }

    initializeQwerty() {
        /*
         * Initialize qwerty keyboard layout.
         */
        let sqSize = 24;
        let padding = 4;
        function kbKeyGenerator(x, y, text) {
            let tile = new ColorTextTile(x, y, Colors.UNGUESSED);
            tile.width = sqSize;
            tile.height = sqSize;
            tile.color = "#4ee954"
            tile.fontSize = sqSize * .8;
            tile.text = text;
            return tile;
        }

        const xOffset = 275;
        const yOffset = 120;

        this.qwerty = {};
        const kbRows = ["qwertyuiop", "asdfghjkl", "zxcvbnm"];
        const kbOffsets = [0, (sqSize + padding) * 0.5, (sqSize + padding) * 1.5]
        kbRows.map((row, y) => {
            row.split("").map((letter ,x) => {
                let xo = xOffset + (sqSize + padding) * x + kbOffsets[y];
                let yo = yOffset + (sqSize + padding) * y;
                this.qwerty[letter] = kbKeyGenerator(xo, yo, letter);
            });
        });
        let values = Object.values(this.qwerty);
        console.log(values);
        this.gameView.addObjects(...values);
    }

    handleWord(data) {
        if (!game.started) return;

        if (data.player === null) {
            data.word.split("").map((letter, idx) => {
                game.answerBar[idx].text = letter;
            });
            return;
        }

        for (let i = 0; i < WORD_LENGTH; i++) {
            game.tiles[game.displayPointerY][i].fillColor = Colors.GUESSED;
        }
        data.correct_character.forEach((idx) => {
            game.tiles[game.displayPointerY][idx].fillColor = "#b8890b";
        });
        data.correct_position.forEach((idx) => {
            game.tiles[game.displayPointerY][idx].fillColor = "#55ae1e";
        });
        data.word.split("").map((letter, idx) => {
            game.tiles[game.displayPointerY][idx].text = letter;
            game.qwerty[letter].fillColor = Colors.GUESSED;
        })

        game.displayPointerY += 1;
    }

    update_players(players) {
        this.playerView.objects = {};
        let height = 30;
        let offset = 150;
        players.map((player, i) => {
            let playerText = new DrawableText(50, offset + height * i)
            playerText.fontSize = height * 0.8;
            playerText.color = player.guessed ? "#090" : "#099";
            playerText.text = `${player.name}: ${player.points} points`;
            this.playerView.addObjects(playerText);
        });

        console.log("Updated players: ", players);
    }
}

let keyPressState = {};
document.addEventListener("keydown", (ev) => {
    keyPressState[ev.key] = true;
});
document.addEventListener("keyup", (ev) => {
    keyPressState[ev.key] = false;
});

function handleInput() {
    // Dont send input if we already guessed this word.
    if (game.correct) return;

    // Handle input
    const validLetters = "qwertyuiopasdfghjklzxcvbnm";


    let arr = validLetters.split("");
    arr.forEach((letter) => {
        if (keyPressState[letter] && game.textPointerX < WORD_LENGTH) {
            game.guessBar[game.textPointerX].text = letter;
            game.textPointerX += 1;
        }
    });
    if (keyPressState["Backspace"] && game.textPointerX > 0) {
        game.textPointerX -= 1;
        game.guessBar[game.textPointerX].text = "";
    }

    if (keyPressState["Enter"] && game.textPointerX === WORD_LENGTH) {
        let word = "";
        for (let i = 0; i < WORD_LENGTH; i++) {
            word += game.guessBar[i].text;
            game.guessBar[i].text = "";
        }
        console.log("Sending", word);
        socket.emit("word", {
            word: word,
            room: ROOM_ID
        })
        game.textPointerX = 0;
    }

    // I never want multiple inputs to happen unless a new down-press occurs.
    keyPressState = {};
}

// Game rendering stuff
let then = 0;

function gameLoop() {
    requestAnimationFrame(gameLoop);

    const now = performance.now();
    const elapsed = now - then;

    // if enough time has elapsed, draw the next frame
    if (elapsed > FPS_INTERVAL) {
        handleInput();

        // Get ready for next frame by setting then=now, but also adjust for your
        // specified fpsInterval not being a multiple of RAF's interval (16.7ms)
        then = now - (elapsed % FPS_INTERVAL);

        // Resizing the canvas should overwrite the width and height variables
        // It has to be a multiple of 2 to remove artifacts around the tilesets
        canvas.width = Math.round(canvas.clientWidth / 2) * 2;
        canvas.height = Math.round(canvas.clientHeight / 2) * 2;

        if (canvas.width !== game.gameView.width || canvas.height !== game.gameView.height) {
            game.gameView.width = canvas.width;
            game.gameView.height = canvas.height;
        }

        // Clear the canvas and fill with floor tile color.
        context.clearRect(0, 0, canvas.width, canvas.height);

        game.stats.fps.put(game.gameView.fps);
        game.stats.frameTime.put(game.gameView.frametime);

        game.statsText.fps.text = round(game.stats.fps.get()) + " fps";
        game.statsText.stateTime.text = "State update time: " + round(game.stats.stateTime.get()) + " ms";
        game.statsText.ping.text = "Latency: " + round(game.stats.ping.get()) + " ms";
        game.statsText.frameTime.text = "Frame time: " + round(game.stats.frameTime.get()) + " ms";

        game.clock.text = (Math.max(0, game.endTime - Date.now())).toLocaleString();

        // Compute the offset for all tiles, to center rendering on the player.
        try {
            view.render();
        } catch (e) {
            console.log(e);
        }
    }
}


function makeMenu() {
    const button = new Button(50, 50, 100, 50);
    button.setOnClick(canvas, (e) => {
        socket.emit("start", {
            "room": ROOM_ID
        });
    })
    const text = new DrawableText(50 + button.width / 2, 50 + button.height / 2);
    text.centered = true;
    text.fontSize = 15;
    text.text = "Start";
    game.menuView.addObjects(button, text);
    game.menuView.renderable = true;
}

function initialize() {
    // Setup stats view
    game.statsView.addObjects(
        game.statsText.frameTime,
        game.statsText.fps,
        game.statsText.ping,
        game.statsText.stateTime
    );

    makeMenu(game.menuView);
    view.addChild(game.menuView);
    view.addChild(game.gameView);

    setInterval(function () {
        startTime = Date.now();
        socket.emit('ping');
    }, game.STATS_INTERVAL);


    socket.on('pong', function () {
        game.stats.ping.put(Date.now() - startTime);
    });
    socket.on("word", (data) => {
        game.handleWord(data);
    });
    socket.on("start", (data) => {
        game.initialize(data)
    });
    socket.on("players", (data) => {
        game.update_players(data);
    });

    socket.emit("join", {room: ROOM_ID});
    intervalID = requestAnimationFrame(gameLoop);
}

let intervalID;
let startTime;
let game = new Wordle();
let socket = io("/wordle");
initialize();
