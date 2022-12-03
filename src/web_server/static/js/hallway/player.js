import {
    AnimatedSpriteTile,
    DrawableText,
    round,
    SpriteTile,
    Point,
    CircularCooldown, ColorTile,
} from "../engine/engine.js";


export class Card {
    constructor(x, y, w, h) {
        this.cardBack = new ColorTile("#dcc995");

        this.cardName = new DrawableText(0, 0);
        this.cardName.text = "Card Text placeholder"
        this.cardDescription = new DrawableText(0, 0);
        this.cardDescription.text = "Card description placeholder"

        this.x = x;
        this.y = y;
        this.width = w;
        this.height = h;
        this.renderable = true;
    }

    render(context) {
        this.cardBack.x = this.x;
        this.cardBack.y = this.y;
        this.cardBack.width = this.width;
        this.cardBack.height = this.height;

        this.cardName.x = this.x;
        this.cardName.y = this.y;
        this.cardDescription.x = this.x;
        this.cardDescription.y = this.y;

        this.cardBack.render(context);
        this.cardName.render(context);
        this.cardDescription.render(context);
    }
}


export class Player {
    constructor(view, tileSet, colour) {
        this.view = view;
        this.colour = colour;

        this.tileSet = tileSet;
        this.renderable = true;
        this.SIZE = 16;
        this.x = 0;
        this.y = 0;
        this.data = {
            moving: false,
            movement_queue: [],
            ready: 0,
            mana: 0,
            max_mana: 0,
            hp: 0,
            max_hp: 0,
        };

        this.name = new DrawableText(0, 0);
        // Default values
        this.name.centered = true
        this.name.fontSize = 6;
        this.name.color = "#fff";
        this.name.borderColor = "#777";

        this.scoreText = new DrawableText(0, 0);
        this.scoreText.fontSize = 15;
        this.score = -1;

        this.item = null;

        this.hp = new CircularCooldown(0, 0, 6);
        this.hp.mainColour = "rgb(0,0,0)"
        this.hp.secondaryColour = "rgba(245,44,44,0.8)"
        this.hp.textObject.renderable = true;

        this.mana = new CircularCooldown(0, 0, 6);
        this.mana.mainColour = "rgb(0,0,0)"
        this.mana.secondaryColour = "rgba(64,121,239,0.8)"
        this.mana.textObject.renderable = true;

        this.hand = [];

        // Fallback
        this.sprite = new SpriteTile(this.tileSet.tiles[`${this.colour}_0_0`]);
        this.deadSprite = new SpriteTile(this.tileSet.tiles[`${this.colour}_dead`]);
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
        this.data = {...data};

        // If you are the owner, you know this.
        if (data.item !== null && data.item !== undefined)
            this.item = new SpriteTile(this.tileSet.tiles[data.item.name]);
        else
            this.item = null;

        // Set player name
        this.name.text = data.username;
        // Sprite width / 2
        this.name.x = this.x * this.SIZE + 8;
        this.name.y = this.y * this.SIZE - this.name.fontSize;

        // Set hp and mana text and progress bar
        this.hp.x = this.x * this.SIZE;
        this.hp.y = this.y * this.SIZE - this.name.fontSize * 2 - this.hp.radius;
        this.mana.x = this.x * this.SIZE + this.SIZE;
        this.mana.y = this.y * this.SIZE - this.name.fontSize * 2 - this.mana.radius;

        this.hp.progress = this.data.hp / this.data.max_hp;
        this.hp.textObject.text = "" + this.data.hp;
        this.mana.progress = this.data.mana / this.data.max_mana;
        this.mana.textObject.text = "" + this.data.mana;

        this.score = data.stored_items.length;
    }

    setWalkingAnimation(direction, sprites) {
        this.walkAnimations[direction / 90] = new AnimatedSpriteTile(sprites);
    }

    setIdleAnimation(direction, sprites) {
        this.idleAnimations[direction / 90] = new AnimatedSpriteTile(sprites);
    }

    renderMovementArrow(context) {

        if (this.data.movement_queue !== undefined && this.data.movement_queue.length > 0) {

            let start = null;
            let end = {
                x: this.x * this.SIZE + this.SIZE / 2,
                y: this.y * this.SIZE + this.SIZE / 2
            };

            context.save();
            // Style parameters
            context.strokeStyle = this.data.color;

            context.lineCap = "round"
            context.lineWidth = 2;


            context.beginPath();
            context.moveTo(end.x, end.y);

            this.data.movement_queue.forEach(move => {
                start = end;
                end = {
                    x: start.x + move.x * this.SIZE,
                    y: start.y + move.y * this.SIZE
                };
                context.lineTo(end.x, end.y);
            });
            context.stroke();

            // Arrow head variables
            let headSize = 4;
            let angle = Math.atan2(end.y - start.y, end.x - start.x);

            //starting a new path from the head of the arrow to one of the sides of
            //the point
            context.beginPath();
            context.moveTo(end.x, end.y);
            context.lineTo(end.x - headSize * Math.cos(angle - Math.PI / 7),
                end.y - headSize * Math.sin(angle - Math.PI / 7));

            //path from the side point of the arrow, to the other side point
            context.lineTo(end.x - headSize * Math.cos(angle + Math.PI / 7),
                end.y - headSize * Math.sin(angle + Math.PI / 7));

            //path from the side point back to the tip of the arrow, and then
            //again to the opposite side point
            context.lineTo(end.x, end.y);
            context.lineTo(end.x - headSize * Math.cos(angle - Math.PI / 7),
                end.y - headSize * Math.sin(angle - Math.PI / 7));

            //draws the paths created above
            context.stroke();
            context.restore();
        }
    }

    render(context) {
        let sprite = null;

        if (this.data.dead) {
            sprite = this.deadSprite;
        } else if (this.data.moving) {
            sprite = this.walkAnimations[this.data.direction / 90];
        } else
            sprite = this.idleAnimations[this.data.direction / 90];

        if (sprite === null) sprite = this.sprite;

        sprite.x = this.x * this.SIZE;
        sprite.y = this.y * this.SIZE;
        sprite.render(context);

        // Render item on top of players head
        if (this.item !== null) {
            this.item.x = this.x * this.SIZE;
            this.item.y = this.y * this.SIZE - 11;
            this.item.render(context);
        }

        this.renderMovementArrow(context);

        // Render name above player
        this.name.render(context);
        this.hp.render(context);
        this.mana.render(context);

    }
}
