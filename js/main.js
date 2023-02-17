<script>
function play() {
    fetch("/current-playback")
        .then(response => response.json())
        .then(data => {
            console.log(data);
            document.getElementById('song-name').innerHTML = data.name;
            document.getElementById('time-elapsed').innerHTML = data.time + ' ms';
            document.getElementById('song-artist').innerHTML = data.artist;
            document.getElementById('album-cover').src = data.url;
        })
        .catch(error => {
            console.error(error);
        })};
}
function skipinsert() {
    fetch("/skip-insert")
        .then(response => response.json())
        .then(data => {
            console.log(data);
            document.getElementById('song-name').innerHTML = data.name;
            document.getElementById('time-elapsed').innerHTML = data.time + ' ms';
            document.getElementById('song-artist').innerHTML = data.artist;
            document.getElementById('album-cover').src = data.url;
        })
        .catch(error => {
            console.error(error);
        })};
}
window.addEventListener('load', function() {
    play()};
});
</script>