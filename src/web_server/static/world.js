import {Button, DrawableText, RollingAverage, round, View, ColorTile} from "./engine.js";

let canvas = document.getElementById("canvas");
let context = canvas.getContext("2d");
context.webkitImageSmoothingEnabled = false;
context.mozImageSmoothingEnabled = false;
context.imageSmoothingEnabled = false;

const FPS_INTERVAL = 1000 / 60;

const view = new View(context); // Main wrapper view
view.width = canvas.width;
view.height = canvas.height;


class PlayerInfo {
    constructor() {

    }
}

let nCountries = 0;
const SQUARE_SIZE = 10;
let colors = ["red", "blue", "green", "orange", "purple", "yellow"]
class Country {
    constructor(points) {
        this.points = points;
        this.color = colors[nCountries % colors.length];
        nCountries++;
    }

    render(context) {
        context.beginPath();
        context.moveTo(this.points[0][0], this.points[0][1]);
        this.points.forEach((point) => {
            context.lineTo(point[0], point[1]);
        })
        context.closePath();
        context.fillStyle(this.color);
        context.fill();
        context.stroke();
    }
}

class Capture {
    STATS_INTERVAL = 1000 / 10;

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

    countries = [];

    initialize() {

    }


    start(data) {
        this.countries = [];
        data.countries.forEach((points) => {
            let country = new Country(points);
            this.countries.push(country);
        });
    }
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


function initialize() {
    // Setup stats view
    game.statsView.addObjects(
        game.statsText.frameTime,
        game.statsText.fps,
        game.statsText.ping,
        game.statsText.stateTime
    );

    view.addChild(game.gameView);

    setInterval(function () {
        startTime = Date.now();
        socket.emit("ping");
    }, game.STATS_INTERVAL);

    socket.on('pong', function () {
        game.stats.ping.put(Date.now() - startTime);
    });

    socket.on("start", (data) => {
        game.start(data);
    });

    socket.emit("join", {room: ROOM_ID});
    game.initialize();
    intervalID = requestAnimationFrame(gameLoop);
}

let intervalID;
let startTime;
let game = new Capture();
let socket = io("/capture");
let USER_NAME;
let audioFiles = {};

let username = Cookies.get("username");
if (username === undefined) {
    while (username === null || username === undefined) {
        username = prompt("Type your username.");
    }
    Cookies.set("username", username);
}


socket.emit("set_session", {username: username});
socket.on("set_session", (data) => {
    USER_NAME = data;
    initialize();
});

