function play() {
    setInterval(function() {
        fetch("/current-playback")
            .then(response => response.json())
            .then(data => {
                console.log(data);
            })
            .catch(error => {
                console.error(error);
            });
    });
}
$(document).ready(function() {
    play();
});
function loadplayer() {
    setInterval(function() {
        fetch("/load-player")
