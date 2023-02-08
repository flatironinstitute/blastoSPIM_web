
//var DATA_FILE = "./lineage.json";
var SIDE = 1000;
var radius_multiple = 2;

var info, surfaces;
var surface_json_data = null;
var series_json_data = null;
var focus_series = null;
var focus_timestamp = null;

var datasets = [
    {
        json: "json/F27_4.json",
        id: "F27_4",
        series: "F27",
        timestamp: "4",
        description: "8 nuclei stage",
    },
    {
        json: "json/F33_67.json",
        id: "F33_67",
        series: "F33",
        timestamp: "67",
        description: "16 nuclei stage",
    },
    {
        json: "json/F37_104.json",
        id: "F37_104",
        series: "F37",
        timestamp: "104",
        description: "32 nuclei stage",
    },
    {
        json: "json/F40_138.json",
        id: "F40_138",
        series: "F40",
        timestamp: "138",
        description: "64 nuclei stage",
    },
    {
        json: "json/F1_171.json",
        id: "F1_171",
        series: "F1",
        timestamp: "171",
        description: "128 nuclei stage",
    },
];

function load_segmentations() {
    var segmentation = $("#segmentation");
    segmentation.empty();
    var select = $("<select/>").appendTo(segmentation);
    for (var info of datasets) {
        $(`<option value="${info.id}">${info.id}: ${info.description}</option>`).appendTo(select);
    }
    var select_change = function () {
        var val = select.find(":selected").val();
        load_id(val);
    };
    select.on("change", select_change)
};

function load_id(data_id) {
    var info = null;
    for (var test_info of datasets) {
        if (test_info.id == data_id) {
            info = test_info
        }
    }
    if (!info) {
        throw new Error("id not found: " + data_id);
    }
    var header = $("#main_header");
    header.html(info.id + " :: " + info.description);
    load_surfaces(info.json, info.series, info.timestamp);
};

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
    var no_download = true;
    info.html("series loaded.");
    series_json_data = data;
    var target_div = $("#volumes");
    focus_on_timestamp(focus_series, focus_timestamp, target_div, data, no_download);
};
