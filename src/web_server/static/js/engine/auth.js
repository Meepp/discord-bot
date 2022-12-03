export function getUsername() {
    let username = Cookies.get("username");
    if (username === undefined) {
        while (username === null || username === undefined) {
            username = prompt("Type your username.");
        }
        Cookies.set("username", username);
    }
    return username;
}

