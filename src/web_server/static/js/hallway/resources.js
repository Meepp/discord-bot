export const COLORS = ["blue", "red", "green", "purple", "black"];


export class TileSet {
    constructor() {
    }
    tiles = {};

    splitTileset(tileSet) {
        let canvas = document.createElement("canvas");
        canvas.className = "disable-anti-aliasing";
        canvas.width = tileSet.width * 3;
        canvas.height = tileSet.height * 3;
        let context = canvas.getContext("2d");

        context.clearRect(0, 0, canvas.width, canvas.height);
        context.webkitImageSmoothingEnabled = false;
        context.mozImageSmoothingEnabled = false;
        context.imageSmoothingEnabled = false;

        context.scale(3, 3);
        context.drawImage(tileSet, 0, 0);

        const S = 48;

        this.tiles["edge_b"] = context.getImageData(6 * S, S, S, S);
        this.tiles["edge_b_top"] = context.getImageData(6 * S, 0, S, S);
        this.tiles["edge_b_alt1"] = context.getImageData(8 * S, 5 * S, S, S);
        this.tiles["edge_b_alt1_top"] = context.getImageData(8 * S, 4 * S, S, S);
        this.tiles["edge_b_alt2"] = context.getImageData(9 * S, 5 * S, S, S);
        this.tiles["edge_b_alt2_top"] = context.getImageData(9 * S, 4 * S, S, S);
        this.tiles["edge_b_alt3"] = context.getImageData(5 * S, 4 * S, S, S);

        this.tiles["corner_br"] = context.getImageData(9 * S, 3 * S, S, S);
        this.tiles["corner_br_top"] = context.getImageData(9 * S, 2 * S, S, S);

        this.tiles["corner_bl"] = context.getImageData(8 * S, 3 * S, S, S);
        this.tiles["corner_bl_top"] = context.getImageData(8 * S, 2 * S, S, S);

        this.tiles["corner_tr"] = context.getImageData(9 * S, S, S, S);
        this.tiles["corner_tr_top"] = context.getImageData(9 * S, 0, S, S);

        this.tiles["corner_tl"] = context.getImageData(8 * S, S, S, S);
        this.tiles["corner_tl_top"] = context.getImageData(8 * S, 0, S, S);

        this.tiles["inner_corner_br"] = context.getImageData(7 * S, 3 * S, S, S);
        this.tiles["inner_corner_br_top"] = context.getImageData(7 * S, 2 * S, S, S);

        this.tiles["inner_corner_bl"] = context.getImageData(5 * S, 3 * S, S, S);
        this.tiles["inner_corner_bl_top"] = context.getImageData(5 * S, 2 * S, S, S);

        this.tiles["inner_corner_tr"] = context.getImageData(7 * S, S, S, S);
        this.tiles["inner_corner_tr_top"] = context.getImageData(7 * S, 0, S, S);

        this.tiles["inner_corner_tl"] = context.getImageData(5 * S, S, S, S);
        this.tiles["inner_corner_tl_top"] = context.getImageData(5 * S, 0, S, S);

        this.tiles["edge_t"] = context.getImageData(6 * S, 3 * S, S, S);
        this.tiles["edge_t_alt1"] = context.getImageData(7 * S, 5 * S, S, S);

        this.tiles["edge_l"] = context.getImageData(7 * S, 2 * S, S, S);
        this.tiles["edge_l_alt1"] = context.getImageData(6 * S, 4 * S, S, S);
        this.tiles["edge_l_alt2"] = context.getImageData(7 * S, 4 * S, S, S);

        this.tiles["edge_r"] = context.getImageData(5 * S, 2 * S, S, S);
        this.tiles["void"] = context.getImageData(S, S, S, S);
        this.tiles["edge_t"] = context.getImageData(6 * S, 3 * S, S, S);

        this.tiles["floor"] = context.getImageData(6 * S, 2 * S, S, S);
        this.tiles["wall_test"] = context.getImageData(6 * S, S, S, S);

        this.tiles["door"] = context.getImageData(7 * S, 7 * S, S, S);
        this.tiles["ladder"] = context.getImageData(15 * S, 8 * S, S, S);
        this.tiles["camera"] = context.getImageData(7 * S, 6 * S, S, S);

        this.tiles["UI_corner_bl"] = context.getImageData(19 * S, 11 * S, S, S);
        this.tiles["UI_edge_left"] = context.getImageData(20 * S, 11 * S, S, S);
        this.tiles["UI_edge_bottom"] = context.getImageData(21 * S, 11 * S, S, S);

        COLORS.map((color, row) => {
            for (let i = 0; i < 3; i++) {
                this.tiles[color + "_90_" + i] = context.getImageData(i * S, (11 + row) * S, S, S);
                this.tiles[color + "_270_" + i] = context.getImageData((i + 3) * S, (11 + row) * S, S, S);
                this.tiles[color + "_180_" + i] = context.getImageData((i + 6) * S, (11 + row) * S, S, S);
                this.tiles[color + "_0_" + i] = context.getImageData((i + 9) * S, (11 + row) * S, S, S);
            }
            this.tiles[color + "_dead"] = context.getImageData(12 * S, (11 + row) * S, S, S);

            // Base chest sprite without animation
            this.tiles["chest_" + color] = context.getImageData(13 * S, (11 + row) * S, S, S);
            for (let i = 0; i < 6; i++) {
                this.tiles["chest_" + color + "_" + i] = context.getImageData((i + 13) * S, (11 + row) * S, S, S);
            }
        });

        COLORS.map((color, i) => {
            this.tiles["collector_" + color] = context.getImageData((19 + i) * S, 6 * S, S, S);
        });

        for (let i = 0; i < 4; i++) {
            this.tiles["rubbish_" + i] = context.getImageData((i + 15) * S, 7 * S, S, S);
        }

        // Load all enemies into the tiles object
        for (let i = 0; i < 3; i++) {
            this.tiles["slime_east_" + i] = context.getImageData(i * S, 16 * S, S, S);
            this.tiles["slime_west_" + i] = context.getImageData((i + 3) * S, 16 * S, S, S);
            this.tiles["slime_south_" + i] = context.getImageData((i + 6) * S, 16 * S, S, S);
            this.tiles["slime_north_" + i] = context.getImageData((i + 9) * S, 16 * S, S, S);
        }

        // Load all spells into the tiles object
        for (let i = 0; i < 2; i++) {
            this.tiles["spear_270_" + i] = context.getImageData((19 + i + 0) * S, 12 * S, S, S);
            this.tiles["spear_0_" + i] = context.getImageData((19 + i + 2) * S, 12 * S, S, S);
            this.tiles["spear_180_" + i] = context.getImageData((19 + i + 4) * S, 12 * S, S, S);
            this.tiles["spear_90_" + i] = context.getImageData((19 + i + 6) * S, 12 * S, S, S);
        }


        // Load all images into canvas to be used later
        for (const [title, data] of Object.entries(this.tiles)) {
            canvas.width = data.width;
            canvas.height = data.height;
            context.putImageData(data, 0, 0);

            let image = new Image();
            image.src = canvas.toDataURL();
            this.tiles[title] = image;
        }

        console.log("Done loading images.");
    }
}


export async function loadImages(src, callback) {
    return new Promise((resolve, reject) => {
        let image = new Image();
        image.onload = () => {
            callback(image);
            resolve();
        };
        image.onerror = reject;
        image.src = src;
    });
}
