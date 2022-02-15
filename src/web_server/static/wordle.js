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

class Wordle {
    tiles = new Array(MAX_GUESSES);

    playerView = new View(context); // Player menu view
    gameView = new View(context); // Game view

    statsView = new View(context); // Informative stats view (fps etc)
    STATS_INTERVAL = 1000 / 10;
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
    textPointer = {
        x: 0,
        y: 0
    }

    initialize() {
        this.gameView.addChild(this.statsView);
        this.gameView.zoom = 1;
        this.gameView.renderable = true;

        view.addChild(this.playerView);
        view.addChild(this.gameView);

        let square_size = 48;
        let padding = 4;
        for (let y = 0; y < MAX_GUESSES; y++) {
            this.tiles[y] = new Array(WORD_LENGTH);
            for (let x = 0; x < WORD_LENGTH; x++) {
                let tile = new ColorTextTile(x * (square_size + padding), y * (square_size + padding), "#999");
                tile.width = square_size;
                tile.height = square_size;
                tile.fontSize = square_size * .8;
                tile.text = ""
                this.tiles[y][x] = tile;
            }
        }

        for (let y = 0; y < MAX_GUESSES; y++) {
            game.gameView.addObjects(...game.tiles[y])
        }
    }

    handleWord(data) {
        data.correct_character.forEach((idx) => {
            game.tiles[game.textPointer.y][idx].fillColor = "#b8890b";
        });
        data.correct_position.forEach((idx) => {
            game.tiles[game.textPointer.y][idx].fillColor = "#55ae1e";
        });
        data.word.split("").map((letter, idx) => {
            game.tiles[game.textPointer.y][idx].text = letter;
        })
        game.textPointer.y += 1;
        game.textPointer.x = 0;
    }
}

function handleInput() {
    // Handle input
    const validLetters = "qwertyuiopasdfghjklzxcvbnm";


    let arr = validLetters.split("");
    arr.forEach((letter) => {
        if (keyState[letter] && game.textPointer.x < WORD_LENGTH) {
            game.tiles[game.textPointer.y][game.textPointer.x].text = letter;
            game.textPointer.x += 1;
        }
    });
    if (keyState["Backspace"] && game.textPointer.x > 0) {
        game.textPointer.x -= 1;
        game.tiles[game.textPointer.y][game.textPointer.x].text = "";
    }

    if (keyState["Enter"] && game.textPointer.x === WORD_LENGTH) {
        let word = "";
        for (let i = 0; i < WORD_LENGTH; i++) {
            word += game.tiles[game.textPointer.y][i].text;
        }
        console.log("Sending", word);
        socket.emit("word", {
            word: word,
            room: ROOM_ID
        })
    }

    // I never want multiple inputs to happen unless a new down-press occurs.
    keyState = {};
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

        // Compute the offset for all tiles, to center rendering on the player.
        try {
            view.render();
        } catch (e) {
            console.log(e);
        }
    }
}


function initialize() {
    // Setup stats view
    game.statsView.addObjects(
        game.statsText.frameTime,
        game.statsText.fps,
        game.statsText.ping,
        game.statsText.stateTime
    );

    game.initialize();

    setInterval(function () {
        startTime = Date.now();
        socket.emit('ping');
    }, game.STATS_INTERVAL);


    socket.on('pong', function () {
        game.stats.ping.put(Date.now() - startTime);
    });

    socket.on("word", game.handleWord);

    socket.emit("start", {"room": ROOM_ID})

    intervalID = requestAnimationFrame(gameLoop);
}
let intervalID;
let game = new Wordle();
let socket = io("/wordle");
initialize();
