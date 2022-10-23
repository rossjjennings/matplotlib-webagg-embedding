/* script for loading matplotlib figure */

/* This is a callback that is called when the user saves
    (downloads) a file.  Its purpose is really to map from a
    figure and file format to a url in the application. */
function ondownload(figure, format) {
window.open('download.' + format, '_blank');
};

function ready(fn) {
if (document.readyState != "loading") {
    fn();
} else {
    document.addEventListener("DOMContentLoaded", fn);
}
}

ready(
function() {
    /* It is up to the application to provide a websocket that the figure
        will use to communicate to the server.  This websocket object can
        also be a "fake" websocket that underneath multiplexes messages
        from multiple figures, if necessary. */
    var websocket_type = mpl.get_websocket_type();
    var websocket = new websocket_type("{{ sock_uri }}");

    // mpl.figure creates a new figure on the webpage.
    var fig = new mpl.figure(
        // A unique numeric identifier for the figure
        {{ fig_id }},
        // A websocket object (or something that behaves like one)
        websocket,
        // A function called when a file type is selected for download
        ondownload,
        // The HTML element in which to place the figure
        document.getElementById("figure"));
}
);
