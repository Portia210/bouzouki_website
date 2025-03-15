function activateIframe(song, event) {
    event.preventDefault();
    var song_iframe = document.getElementById('iframe-song');
    var sheet_iframe = document.getElementById('iframe-sheet');
    var more_results = document.getElementById('more-videos');
    var song_name_elem = document.getElementById('song_name');

    // Replace the iframe source with the specified demo ID
    more_results.href = song.more_videos;
    song_name_elem.textContent = song.song_en_name;
    replaceIframeContent(song_iframe, 'https://www.youtube.com/embed/' + song.video_id);
    replaceIframeContent(sheet_iframe, 'https://www.youtube.com/embed/' + song.demo_id);
}

function replaceIframeContent(iframe, newSrc) {
    iframe.src = newSrc;
}

// Load the first song when the page loads
window.onload = function() {
    var firstSongLink = document.querySelector('.list-group-item a');
    if (firstSongLink) {
        firstSongLink.click();
    }

    // Scroll to the anchor if it exists
    if(window.location.hash) {
        var anchor = decodeURIComponent(window.location.hash);
        var element = document.querySelector(anchor);
        if(element) {
            element.scrollIntoView({behavior: "smooth"});
            // Activate the iframe for the selected song
            element.querySelector('a').click();
        }
    }
};