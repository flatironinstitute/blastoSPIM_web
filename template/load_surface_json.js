
//var DATA_FILE = "./lineage.json";
var SIDE = 1000;
var radius_multiple = 2;

var info, surfaces;
var surface_json_data = null;
var series_json_data = null;
var focus_series = null;
var focus_timestamp = null;

function load_surfaces(file_path, series, timestamp) {
    focus_series = series;
    focus_timestamp = timestamp;
    info = $("#info");
    surfaces = $("#surfaces");
    var header = $("#main_header");
    header.html(`Segmentation detail for series ${series} timestamp ${timestamp}`)
    surfaces.width(SIDE).height(SIDE);
    surfaces.css({"border-style": "solid"});
    surfaces.css("background-color", "cyan")
    info.html("loading: " + file_path);
    var on_load_failure = function() {
        alert("Could not load local surface JSON data.\n" +
                "You may need to run a web server to avoid cross origin restrictions.")
    };
    $.getJSON(file_path, setup_json).fail(on_load_failure);
};

var setup_json = function(data) {
    debugger;
    //var DATA_FILE = '../test_site/data/manifest.json';
    surface_json_data = data;
    info.html("surface loaded.");
    // also load series json
    var on_load_failure = function() {
        alert("Could not load local series JSON data.\n" +
                "You may need to run a web server to avoid cross origin restrictions.")
    };
    $.getJSON(DATA_FILE, setup_series).fail(on_load_failure);
    var container = surfaces;
    var display3d = container.surfaces_sequence(data);
    display3d.load_3d_display(container);
};

var setup_series = function(data) {
    info.html("series loaded.");
    series_json_data = data;
    var target_div = $("#volumes");
    focus_on_timestamp(focus_series, focus_timestamp, target_div, data);
};
