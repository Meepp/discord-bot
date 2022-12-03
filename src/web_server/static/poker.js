const CURRENCY = "¤";

let canvas = document.getElementById("canvas");
canvas.width = 1000;
canvas.height = 600;
let context = canvas.getContext("2d");
context.imageSmoothingEnabled = true;

let socket = io("/poker");

socket.on("join", (data) => {
    console.log(`${data} joined the room.`);
});

socket.on("leave", (data) => {
    console.log(`${data} left the room.`);
});


$('#messageform').submit(function(e) {
    e.preventDefault(); // prevents page reloading
    let m = $('#m');
    data = {
        "message": m.val(),
        "room": $('#roomid').val(),
        "username": $('#username').val()
    };

    console.log(data)
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

const CARD_WIDTH = 222;
const CARD_HEIGHT = 323;
let COMMUNITY_CARD_FLIP_MAXTICKS = 30;
let INITIAL_COMMUNITY_CARD_FLIPTICKS = [
    COMMUNITY_CARD_FLIP_MAXTICKS,
    COMMUNITY_CARD_FLIP_MAXTICKS * 1.5,
    COMMUNITY_CARD_FLIP_MAXTICKS * 2,
    COMMUNITY_CARD_FLIP_MAXTICKS,
    COMMUNITY_CARD_FLIP_MAXTICKS
];

function getRelativeMousePosition(canvas, evt) {
    let rect = canvas.getBoundingClientRect();
    return {
        x: evt.clientX - rect.left,
        y: evt.clientY - rect.top
    };
}

function PokerTable() {
    this.hand = [];
    this.state = {
        community_cards: [],
        hand: [],
        players: [{
            "state": "",
            "balance": 0,
            "name": "",
            "hand": null,
        }],
        active_player: "",
        started: false,
        you: "name",
        balance: 0,
        to_call: 0,
        settings: {
            max_buy_in: 0,
            small_blind_value: 0
        }
    };

    this.community_card_flip_ticks = [...INITIAL_COMMUNITY_CARD_FLIPTICKS];

	this.nMessages = 0;
    this.fadeMessages = [];

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


function drawPlayerHand(i, player) {
    /*
     * This supports up to 7 other player hands.
     */
    let positions = [
        {x: 158, y: 410},
        {x: 108, y: 243},
        {x: 196, y: 122},
        {x: 586, y: 93.26666259765625},
        {x: 853, y: 169.26666259765625},
        {x: 888, y: 347.26666259765625},
        {x: 765, y: 479.26666259765625}
    ];

    let pos = positions[i];

    const cardWidth = CARD_WIDTH * .4;

    context.translate(pos.x, pos.y);
    // 0.785398163 == 45 radians
    context.rotate((i + 1) * 0.785398163);
    if (player.hand === null) {
        context.drawImage(images["cardback"], 0, 0, cardWidth, CARD_HEIGHT * .4);
        context.drawImage(images["cardback"], 20, 10, cardWidth, CARD_HEIGHT * .4);
    } else {
        context.fillStyle = "beige";
        context.fillRect(0, 0, cardWidth, CARD_HEIGHT * .4);
        context.drawImage(images[`${player.hand[0].rank}_of_${player.hand[0].suit}`], 0, 0, cardWidth, CARD_HEIGHT * .4);
        context.fillRect(20, 10, cardWidth, CARD_HEIGHT * .4);
        context.drawImage(images[`${player.hand[1].rank}_of_${player.hand[1].suit}`], 20, 10, cardWidth, CARD_HEIGHT * .4);
    }

    if (!player.active)
        context.fillStyle = "black";
    else
        context.fillStyle = "darkred";

    if (i >= 2 && i <= 4) {
        // Flip text drawing right side up
        context.rotate(3.141592652);
        context.translate(-cardWidth, 60);
    }

    context.font = "20px Arial";
    context.fillText(player.color, 0, -36);
    context.font = "16px Arial";
    context.fillText(player.state + " | " + CURRENCY + player.balance, 0, -16);

    if (i >= 2 && i <= 4) {
        context.translate(cardWidth, -60);
        context.rotate(-3.141592652);
    }

    context.rotate((i + 1) * -0.785398163);
    context.translate(-pos.x, -pos.y);
}


// Game rendering stuff
function render() {
    context.clearRect(0, 0, canvas.width, canvas.height);

    // Draw background
    context.drawImage(images["board"], 0, 0, canvas.width, canvas.height);

    for (let i = 0; i < pokerTable.state.community_cards.length; i++) {
        placeCommunityCard(i);
    }

    // Get your position on the table.
    let userPos = -1;
    for (let i = 0; i < pokerTable.state.players.length; i++) {
        if (pokerTable.state.you === pokerTable.state.players[i].name) {
            userPos = i;
        }
    }

    // Place other players cards relative to your position
    for (let i = 0; i < pokerTable.state.players.length; i++) {
        if (pokerTable.state.you === pokerTable.state.players[i].name) continue;

        let pos = i;
        if (pos > userPos) pos--;

        pos = (pos - userPos + 7) % 7;

        let player = pokerTable.state.players[i];
        drawPlayerHand(pos, player);
    }

    let handCardWidth = 100;
    let handCardHeight = 150;
    for (let i = 0; i < pokerTable.state.hand.length; i++) {
        let x = 400 + i * 110;
        let y = 450;
        context.fillStyle = "beige";
        context.fillRect(x, y, handCardWidth, handCardHeight);
        let image_name = `${pokerTable.state.hand[i].rank}_of_${pokerTable.state.hand[i].suit}`;
        context.drawImage(images[image_name], x, y, handCardWidth, handCardHeight);
    }

    context.fillStyle = "black";
    context.font = "20px Arial";
    context.fillText(`Current turn: ${pokerTable.state.active_player}`, 10, 20);
    context.fillText(`Pot: ${CURRENCY}${pokerTable.state.pot}`, 420, 180);
    context.font = "30px Arial";
    context.fillText(`${CURRENCY}${pokerTable.state.balance}`, 420, 400);

    pokerTable.drawFadeMessages();

}

function placeCommunityCard(index) {
    let img_name = `${pokerTable.state.community_cards[index].rank}_of_${pokerTable.state.community_cards[index].suit}`;
    let card = images[img_name];

    let x = 283.5 + 85.5 * index;
    let y = 258;
    let tableCardWidth = 60;
    let tableCardHeight = 90;

    if (pokerTable.community_card_flip_ticks[index] === COMMUNITY_CARD_FLIP_MAXTICKS) {
        audioFiles[`flip_card_${index % 2}`].currentTime = 0.0;
        audioFiles[`flip_card_${index % 2}`].play();
    }

    context.fillStyle = "beige";
    if (pokerTable.community_card_flip_ticks[index] > 0) {
        let half = COMMUNITY_CARD_FLIP_MAXTICKS / 2;
        let ticks = pokerTable.community_card_flip_ticks[index]--;
        // First half of turning animation (back side up)

        let animation_percent = Math.sin(Math.min((ticks - half), COMMUNITY_CARD_FLIP_MAXTICKS - half) / half * Math.PI / 2);
        let width = tableCardWidth * animation_percent;
        let yOffset = -(1 - Math.abs(animation_percent)) * 7;

        let xOffset = (tableCardWidth - width) / 2 - (-(1 - Math.abs(animation_percent)) * 7);
        if (ticks > half) {
            context.drawImage(images["cardback"], x + xOffset, y + yOffset, width, tableCardHeight);
        } else {
            context.fillRect(x + xOffset, y + yOffset, width, tableCardHeight);
            context.drawImage(card, x + xOffset, y + yOffset, width, tableCardHeight);
        }
    } else {
        // Flat card on the table
        context.fillRect(x, y, tableCardWidth, tableCardHeight);
        context.drawImage(card, x, y, tableCardWidth, tableCardHeight);
    }
}

let images = {};
let audioFiles = {};
let pokerTable = new PokerTable();

function initialize() {
    /*
     * Preload all images to reduce traffic later.
     */
    const ranks = ["ace", "king", "queen", "jack", "10", "9", "8", "7", "6", "5", "4", "3", "2"];
    const suits = ["hearts", "spades", "clubs", "diamonds"];
    let nLoads = 2;

    images["board"] = new Image();
    images["board"].onload = () => {
        nLoads--;
        if (nLoads === 0) postInit()
    };
    images["board"].src = `/static/images/board.png`;

    images["cardback"] = new Image();
    images["cardback"].onload = () => {
        nLoads--;
        if (nLoads === 0) postInit()
    };
    images["cardback"].src = `/static/images/cards/back.png`;

    ranks.forEach(rank => {
        suits.forEach(suit => {
            let card = `${rank}_of_${suit}`;
            images[card] = new Image();
            images[card].onload = () => {
                nLoads--;
                if (nLoads === 0) postInit()
            };
            images[card].src = `/static/images/cards/${card}.png`;
            nLoads++;
        });
    });

    audioFiles["flip_card_0"] = new Audio(`/static/audio/flip_card.mp3`);
    audioFiles["flip_card_1"] = new Audio(`/static/audio/flip_card.mp3`);
    audioFiles["begin"] = new Audio(`/static/audio/begin.mp3`);
    audioFiles["notify"] = new Audio(`/static/audio/notify.mp3`);

    /*
     * Register all socket.io functions to the pokerTable object.
     */
    socket.on("table_state", (data) => {
        console.log("Received table state.");
        // Check before overwriting state.
        if (pokerTable.state.active_player !== USER_NAME && data.active_player === USER_NAME) {
            audioFiles["notify"].play();
        }
        pokerTable.setState(data);

        rangeSlider.max = pokerTable.state.balance;

        document.getElementById("call-button").innerHTML = "Call with " + (pokerTable.state.to_call)

        if (!pokerTable.state.started) {
            let userList = $(".user-list");
            userList.empty();
            data.players.forEach(player => {
                userList.append(`
                    <div class="user-entry">
                    <div class="user-entry-name">${player.color}</div>
                    <div class="user-entry-balance">${CURRENCY}${player.balance}</div>
                    <div class="user-entry-ready">${player.ready ? "Ready" : "Not Ready"}</div>
                    </div>
                `);
            });

            let settings = document.getElementById("room-settings");
            settings.innerHTML = `<div>   
                <div>Small blind value: ${data.settings.small_blind_value}</div>
                <div>Max buy-in: ${data.settings.max_buy_in}</div>
            </div>`;
        }

    });
    socket.on("message", (data) => {
		pokerTable.nMessages++;
        pokerTable.fadeMessages.push({
            message: data,
            ticks: 120
        });
    });

    console.log("Requesting stable state");
    socket.emit("table_state", {
        "room": ROOM_ID
    });
}

function postInit() {
}


function raise() {
    sendAction("raise", rangeSlider.value);
}

function fold() {
    sendAction("fold", 0);
}

function call() {
    sendAction("call", 0);
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

function startRoom() {
    if (!pokerTable.state.started) {
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
    // Reset flip animation ticks
    pokerTable.community_card_flip_ticks = [...INITIAL_COMMUNITY_CARD_FLIPTICKS];
    audioFiles["begin"].play();
});

socket.emit("join", {
    "room": ROOM_ID,
});

initialize();

socket.on("message", (data) => {
    let log = document.getElementById("event-log");
	let events = log.getElementsByTagName('div');
	if (events.length > 100) {
		events[0].remove();
	}
    log.innerHTML += `
    <div class="event-log-entry">
        <div class="event-log-date">${new Date().toLocaleTimeString()}</div>
        <div class="event-log-value">${data}</div>
    </div>`;

    log.lastChild.scrollIntoView();
});


/*
 * Load slider stuff
 */
let rangeSlider = document.getElementById("rs-range-line");
let rangeBullet = document.getElementById("rs-bullet");

rangeSlider.addEventListener("input", showSliderValue, false);

function showSliderValue() {
    if (rangeSlider.value === rangeSlider.max) {
        rangeBullet.innerHTML = "All In"
    } else {
        rangeBullet.innerHTML = rangeSlider.value;
    }
    let bulletPosition = (rangeSlider.value / rangeSlider.max);
    rangeBullet.style.left = (bulletPosition * 200) + "px";
}

function changeSettings() {
    let data = {
        room_id: ROOM_ID,
        settings: {
            small_blind_value: document.getElementById("small-blind-value").value,
            max_buy_in: document.getElementById("max-buy-in").value,
        }
    };
    socket.emit("change settings", data)
}

document.addEventListener("keydown", (ev) => {
    let increment = 1;
    if (ev.ctrlKey) {
        increment = 10;
    } else if (ev.shiftKey) {
        increment = 50;
    }

    if (ev.key === "ArrowLeft") {
        rangeSlider.value -= increment;
    } else if (ev.key === "ArrowRight") {
        rangeSlider.value = 1 * rangeSlider.value + increment;
    } else if (ev.key === "c") {
        call();
    } else if (ev.key === "r") {
        raise();
    } else if (ev.key === "f") {
        fold();
    } else if (ev.key === "b") {
        toggleReady();
    }
    showSliderValue();
});
