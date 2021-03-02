class DefaultListDict {
    constructor() {
        return new Proxy({}, {
            get: (target, name) => name in target ? target[name] : []
        })
    }
}


class Point {
    constructor(x, y) {
        this.x = x;
        this.y = y;
    }
}

class Rectangle extends Point {
    constructor(x, y, width, height) {
        super(x, y);
        this.width = width;
        this.height = height;
    }
}

class Circle extends Point {
    constructor(x, y, radius) {
        super(x, y);
        this.radius = radius;
    }
}

class SpriteTile extends Rectangle {
    constructor(image) {
        super(0, 0, 16, 16);
        this.image = "";
        this.setImage(image);
        this.renderable = false;
    }

    render(context) {
        context.drawImage(this.image, this.x, this.y, this.width, this.height);
    }

    setImage(image) {
        if (!(image instanceof Image))
            throw Error("Must give object instanceof class Image.");

        this.image = image;
    }
}

class AnimatedSpriteTile extends SpriteTile {
    constructor(images) {
        if (images.length === 0) throw Error("AnimatedSpriteTile must have at least one image.");
        super(images[0]);

        this.frame = 0;
        this.frameTime = 6; // N ticks per frame
        this.images = images;
    }

    render(context) {
        this.frame = (this.frame + 1) % (this.images.length * this.frameTime);
        this.setImage(this.images[Math.floor(this.frame / this.frameTime)]);
        super.render(context);
    }
}

class CircularCooldown extends Circle {
    /*
     * The progress property defines how far the cooldown is along.
     * Range is 0-1.
     */
    constructor(x, y, radius) {
        super(x, y, radius);
        this.progress = 0;
        this.mainColour = "#418eb0";
        this.secondaryColour = "#3f3656";

        this.renderable = true;
        this.textObject = new DrawableText(x, y);
        this.textObject.centered = true;
    }

    render(context) {
        context.lineWidth = 15;
        context.strokeStyle = this.mainColour;
        context.beginPath();
        context.arc(this.x, this.y, this.radius, 0, 2 * Math.PI);
        context.stroke();

        context.lineWidth = 13;
        context.strokeStyle = this.secondaryColour;
        context.beginPath();
        context.arc(this.x, this.y, this.radius, 0, 2 * Math.PI * this.progress);
        context.stroke();

        if (this.textObject !== null) {
            // TODO: Dont set these properties here.
            this.textObject.fontSize = 25;
            this.textObject.color = "#fff";
            this.textObject.render(context);
        }
    }
}


class ColorTile extends Rectangle {
    constructor(color) {
        super(0, 0, 16, 16);
        this.color = color;
    }

    render(context) {
        context.fillStyle = this.color;
        context.fillRect(this.x, this.y, this.width, this.height);
    }
}

class DrawableText extends Point {
    constructor(x, y) {
        super(x, y);
        this.text = "test";
        this.fontSize = 12;
        this.font = "Arial";
        this.color = "#F00";
        this.renderable = true;
        this.centered = false;
    }

    render(context) {
        context.font = `${this.fontSize}px ${this.font}`;
        context.fillStyle = this.color;

        if (this.centered === true) {
            let width = context.measureText(this.text).width;
            context.fillText(this.text, this.x - width / 2, this.y + this.fontSize * .33);
        } else {
            context.fillText(this.text, this.x, this.y + this.fontSize / 2);
        }
    }
}


class View {
    constructor(context) {
        this.cameraCenter = new Point(400, 400);

        this.width = 800;
        this.height = 800;
        this.zoom = 1;
        this.context = context;
        this.objects = [[], [], [], []];
        this.renderable = true;

        this.children = [];
        this.frametime = 0;
        this.fps = 0;


        this._lastInvokation = 0;
    }

    addChild(child) {
        if (!(child instanceof View))
            throw Error("Must give object instanceof class View.");

        this.children.push(child);
    }

    render() {
        if (!this.renderable) return;

        const start = performance.now();

        const hw = this.width / 2;
        const hh = this.height / 2;
        const xOffset = -this.cameraCenter.x * this.zoom + hw;
        const yOffset = -this.cameraCenter.y * this.zoom + hh;
        this.context.setTransform(this.zoom, 0, 0, this.zoom, xOffset, yOffset);

        this.objects.forEach(l => {
            l.forEach(obj => {
                if (!obj.renderable) return;

                obj.render(this.context);
            })
        });

        this.context.setTransform(1, 0, 0, 1, 0, 0);
        this.children.forEach(child => {child.render()});
        this.frametime = (performance.now() - start);

        this.fps = 1000 / (performance.now() - this._lastInvokation);
        this._lastInvokation = performance.now();
    }
}