  function play() {
            let elapsedTime = 0;
            let timerId;
            clearInterval(timerId)
            fetch("/current-playback")
                .then(response => response.json())
                .then(data => {
                    console.log(data);
                    document.getElementById('song-name').innerHTML = data.name;
                    //document.getElementById('max-duration').innerHTML = data.mtime + ' s';
                    document.getElementById('song-artist').innerHTML = data.artist;
                    document.getElementById('album-cover').src = data.url;
                    elapsedTime = data.time / 1000;
                    maxDuration = data.mtime / 1000;
                    document.getElementById('max-duration').innerHTML = maxDuration + ' s';
                    // document.getElementById('time-elapsed').innerHTML = elapsedTime + ' s';
                    timerId = setInterval(updateTime(elapsedTime, timerId), 1000)
                })
                .catch(error => {
                    console.error(error);
                });
        }

        function updateTime(elapsedTime, timerId) {
            return () => {
                elapsedTime = elapsedTime + 1;
                if (elapsedTime > maxDuration) {
                    clearInterval(timerId)
                    elapsedTime = 0;
                    maxDuration = 0;
                    skipinsert()
                }
                document.getElementById('time-elapsed').innerHTML = elapsedTime + ' s';
            };
        }

        function skipinsert() {
            fetch("/skip-insert")
                .then(response => response.json())
                .then(data => {
                    console.log(data);
                    document.getElementById('time-elapsed').innerHTML = 0;
                    play();
                    document.getElementById('song-name').innerHTML = data.name;
                    document.getElementById('song-artist').innerHTML = data.artist;
                    document.getElementById('album-cover').src = data.url;
                })
                .catch(error => {
                    console.error(error);
                });
        }

        function goback() {
            fetch("/go-back")
                .then(response => response.json())
                .then(data => {
                    console.log(data);
                    document.getElementById('song-name').innerHTML = data.name;
                    document.getElementById('time-elapsed').innerHTML = data.time + '  s';
                    document.getElementById('song-artist').innerHTML = data.artist;
                    document.getElementById('album-cover').src = data.url;
                })
                .catch(error => {
                    console.error(error);
                });
        }

        function pausesong() {
            fetch("/pause-song")
                .then(response => response.json())
                .then(data => {
                    console.log(data);
                    document.getElementById('song-name').innerHTML = data.name;
                    document.getElementById('time-elapsed').innerHTML = data.time + '  s';
                    document.getElementById('song-artist').innerHTML = data.artist;
                    document.getElementById('album-cover').src = data.url;
                })
                .catch(error => {
                    console.error(error);
                });
        }

        function populateRecords() {
            fetch('/toplist')
                .then(response => response.json())
                .then(data => {
                    const table = $('#myTable').DataTable({
                        columns: [
                            {
                                data: "track_url",
                                render: function (data, type, row) {
                                    return '<img src="' + data + '" alt="Album cover" height="64"/>';
                                }
                            },
                            {data: "track_name"},
                            {data: "artist"},
                            {data: "times_played"},
                            {
                                data: "average_duration_played",
                                render: function (data, type, row) {
                                    if (type === 'display') {
                                        return (data / 1000) + ' s';
                                    }
                                    return data;
                                }
                            },
                            {
                                data: "last_duration_played",
                                render: function (data, type, row) {
                                    if (type === 'display') {
                                        return (data / 1000) + ' s';
                                    }
                                    return data;
                                }
                            },
                            {
                                data: "max_duration",
                                render: function (data, type, row) {
                                    if (type === 'display') {
                                        return (data / 1000) + ' s';
                                    }
                                    return data;
                                }
                            }
                        ]
                    });

                    table.rows.add(data).draw();
                })
                .catch(error => console.error(error));
        }

        window.addEventListener('load', function () {
            play();
            populateRecords();
        });