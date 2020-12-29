function askPassword(password, room_id) {
    console.log("got here")
    let input = prompt("Password: ");
    while (input !== password) {
        if (input === null) {
            return
        }
        input = prompt("Password incorrect, please try again: ")
    }

    window.location.replace(`/${room_id}/game`)
}