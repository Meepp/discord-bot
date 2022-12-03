import {
    DrawableText,
    RollingAverage,
    Point, Rectangle, ColorTile, SpriteTile
} from "../engine/engine.js";
import {COLORS} from "./resources.js";
import {Card, Player} from "./player.js";


export class HallwayHunters {
    constructor(view, UIView, tileSet) {
        this.view = view;
        this.UIView = UIView;
        this.tileSet = tileSet;
        this.cards = [];
    }

    state = {
        board_size: 30,
        all_players: [],
        player_data: {
            dead: false,
            name: "",
            class_name: "",
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
            movement_queue: [],
            ability_cooldown: 0,
            ability_timer: 0,
            sprint_cooldown: 0,
            sprint_timer: 0,
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
    lookup = {};
    items = [];

    players = {};

    setState(data) {
        let start = performance.now();
        if (this.state.board.length === 0) {
            this.initializeBoard(data.board_size);
        }

        if (data.visible_tiles !== undefined) {
            this.updateBoardSprites(data.visible_tiles);
            this.updateItems(data.visible_tiles);
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
        data.all_players.forEach(player => {
            this.players[player.color].renderable = true;
            this.players[player.color].update(player);
        });

        const readyStates = ["Ready", "Processing...", "Not Ready"]
        let sum = new Point(0, 0);
        this.state.all_players.forEach(player => {
            const p = this.players[player.color];
            p.score = player.stored_items.length;
            p.scoreText.text = player.username + " " + readyStates[p.data.ready]
            sum.x += player.position.x;
            sum.y += player.position.y;
        });

        // Update new camera center based on average position between all players
        let newCameraCenter = new Point(
            sum.x / this.state.all_players.length * 16,
            sum.y / this.state.all_players.length * 16
        );

        // Camera center as own player location
        // let newCameraCenter = new Point(data.player_data.position.x * 16, data.player_data.position.y * 16);
        if (this.state.started)
            this.updateRenderable(this.view.cameraCenter, newCameraCenter);

        this.view.cameraCenter = newCameraCenter;

        this.stats.stateTime.put(performance.now() - start);
    };


    updateBoardSprites(tiles) {
        tiles.forEach(obj => {
            let oldTile = this.state.board[obj.x][obj.y];
            oldTile.setImage(this.tileSet.tiles[obj.tile.image])
        });
    }

    updateRenderable(oldCenter, newCenter) {
        const w = this.view.width / this.view.zoom;
        const h = this.view.height / this.view.zoom;
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
        let width = Math.min(oldRenderbox.x + oldRenderbox.width, this.state.board_size);
        let height = Math.min(oldRenderbox.y + oldRenderbox.height, this.state.board_size);
        for (let x = oldRenderbox.x; x < width; x++) {
            for (let y = oldRenderbox.y; y < height; y++) {
                this.state.board[x][y].renderable = false;
            }
        }
        // Add the renderable property to the new box
        width = Math.min(newRenderbox.x + newRenderbox.width, this.state.board_size);
        height = Math.min(newRenderbox.y + newRenderbox.height, this.state.board_size);

        // TODO: Dont recompute the entire vision lines every new data update
        this.view.clearLayer(2);
        for (let x = newRenderbox.x; x < width; x++) {
            for (let y = newRenderbox.y; y < height; y++) {
                this.state.board[x][y].renderable = true;

                if (this.lookup[x] === undefined || !this.lookup[x][y]) {
                    let tile = new ColorTile("rgba(0,0,0,0.2)");
                    tile.x = x * 16;
                    tile.y = y * 16;
                    tile.z = 2;
                    tile.renderable = true;

                    this.view.addObjects(tile);
                }
            }
        }
    }


    updateItems(tiles) {
        tiles.forEach(tile => {
            if (this.state.board[tile.x][tile.y].item !== undefined) {
                if (tile.tile.item === null) {
                    // TODO: Remove this object from the renderable list
                    this.state.board[tile.x][tile.y].item.renderable = false;
                    this.state.board[tile.x][tile.y].item = undefined;
                } else {
                    this.state.board[tile.x][tile.y].item.setImage(this.tileSet.tiles[tile.tile.item.name]);
                }
                return;
            }
            if (tile.tile.item !== null) {
                let item = new SpriteTile(this.tileSet.tiles[tile.tile.item.name]);
                // FIXME: Items aren't always renderable, update this.
                item.renderable = true;
                item.x = tile.x * 16;
                item.y = tile.y * 16;
                item.z = 1;
                this.state.board[tile.x][tile.y].item = item;
                this.view.addObjects(item);
            }
        });
    }

    initializeBoard(board_size) {
        for (let x = 0; x < board_size; x++) {
            let list = [];
            for (let y = 0; y < board_size; y++) {
                let sprite = new SpriteTile(this.tileSet.tiles["void"]);
                sprite.x = x * 16;
                sprite.y = y * 16;
                list.push(sprite);
                this.view.addObjects(sprite);
            }
            this.state.board.push(list);
        }
    }

    initializeCards() {
        const MAX_HAND_CARDS = 8;
        // Set cards in hand information
        for (let i = 0; i < MAX_HAND_CARDS; i++) {
            const w = 100;
            const h = 144;
            const padding = 4;
            this.cards.push(new Card(padding + i * (w + padding), this.view.height - h + padding, w, h));
            this.UIView.addObjects(this.cards[i]);
        }
    }

    /*
     * This function should get called when the game has started, and we know how many player entities need to be rendered
     */
    initializePlayers() {
        COLORS.forEach(colour => {
            let player = new Player(
                this.view,
                this.tileSet,
                colour
            );
            [0, 90, 180, 270].forEach(d => {
                player.setWalkingAnimation(d, [
                    this.tileSet.tiles[`${colour}_${d}_0`],
                    this.tileSet.tiles[`${colour}_${d}_1`],
                    this.tileSet.tiles[`${colour}_${d}_0`],
                    this.tileSet.tiles[`${colour}_${d}_2`],
                ]);

                player.setIdleAnimation(d, [
                    this.tileSet.tiles[`${colour}_${d}_0`]
                ]);
            });
            this.players[colour] = player;
        });
    }
}