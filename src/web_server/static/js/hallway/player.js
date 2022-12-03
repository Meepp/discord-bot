import {
    AnimatedSpriteTile,
    DrawableText,
    round,
    SpriteTile,
    Point,
    CircularCooldown, ColorTile, FilledCircle, Button,
} from "../engine/engine.js";


export const MANA_COLOR = "rgba(64,121,239,0.8)";
export const RANGE_COLOR = "#2da128";
export const RADIUS_COLOR = "#9f9730";
export const HP_COLOR = "rgba(245,44,44,0.8)";
export const DAMAGE_COLOR = {
    "prc": "rgba(210,82,82,0.8)",
    "heal": "rgba(153,222,72,0.8)",
    "fire": "rgba(110,16,16,0.8)"
}
export const CARDBACK_HOVER_COLOR = "#c0ae7b";
export const CARDBACK_COLOR = "#dcc995";
export const CARDBACK_SELECTED_COLOR = "#fcedcb";

export class Card {
    constructor(x, y, w, h) {
        this.cardBack = new Button(x, y, w, h);
        this.cardBack.color = CARDBACK_COLOR;
        this.cardBack.hoverColor = CARDBACK_HOVER_COLOR;

        this.cardName = new DrawableText(0, 0);
        this.cardName.text = "Card Text placeholder"
        this.cardName.centered = true;
        this.cardName.color = "rgb(70,53,37)"

        this.cardDescription = new DrawableText(0, 0);
        this.cardDescription.text = "Card description placeholder"
        this.cardDescription.color = "rgb(143,108,76)"
        this.cardDescription.centered = true;

        // Create info balls at the top
        let ringRadius = 10;
        this.manaCost = new FilledCircle(0, 0, ringRadius);
        this.damage = new FilledCircle(0, 0, ringRadius);
        this.range = new FilledCircle(0, 0, ringRadius);
        this.radius = new FilledCircle(0, 0, ringRadius);
        this.manaCost.color = MANA_COLOR;
        this.manaCost.textObject.color = "#000";
        this.damage.color = HP_COLOR;
        this.damage.textObject.color = "#000";
        this.range.color = RANGE_COLOR;
        this.range.textObject.color = "#000";
        this.radius.color = RADIUS_COLOR;
        this.radius.textObject.color = "#000";


        this.x = x;
        this.y = y;
        this.padding = 2;
        this.width = w;
        this.height = h;
        this.renderable = true;
    }

    render(context) {
        // Render cardback
        this.cardBack.render(context);

        // Calculate ring positions
        let ringSize = (this.manaCost.radius + this.padding);

        this.manaCost.x = this.x + ringSize;
        this.damage.x = this.x - ringSize + this.width;
        this.range.x = this.x + (ringSize * 3);
        this.radius.x = this.x - (ringSize * 3) + this.width;
        this.manaCost.y = this.damage.y = this.range.y = this.radius.y = this.y + ringSize;

        // Render rings
        this.manaCost.render(context);
        this.damage.render(context);
        this.range.render(context);
        this.radius.render(context);

        // Calculate text positions
        let textOffset = (ringSize + this.padding) * 2;
        let cardMidWidth = this.x + this.padding + this.width / 2;

        this.cardName.x = this.cardDescription.x = cardMidWidth;
        this.cardName.y = this.y + textOffset;
        this.cardDescription.y = this.y + this.cardName.fontSize + textOffset + this.padding;

        // Render text
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
        this.hp.secondaryColour = HP_COLOR;
        this.hp.textObject.renderable = true;

        this.mana = new CircularCooldown(0, 0, 6);
        this.mana.mainColour = "rgb(0,0,0)"
        this.mana.secondaryColour = MANA_COLOR;
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
