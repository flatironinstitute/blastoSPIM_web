
var info;

var WEB_ROOT = "../test_site/";
var DATA_ROOT = WEB_ROOT + "data/";
var DATA_WEB = DATA_ROOT + "web/";
var DATA_SOURCE = DATA_ROOT + "source/";
var DATA_FILE = DATA_ROOT + "manifest.json"

function setup() {
    info = $('#info');
    info.html("Javascript loaded.");
    $.getJSON(DATA_FILE, process_json).fail(on_load_failure);
};

var on_load_failure = function() {
    alert("Could not load local JSON data.\n" +
            "You may need to run a web server to avoid cross origin restrictions.")
};

var json_data, series_select, series_header, series_detail, model_link;
var timestamp_detail, timestamp_header;
var focus_timestamp = null;
var focus_series = null;
var focus_timestamp = null;

var process_json = function(data) {
    debugger;
    json_data = data;
    info.html("JSON loaded.");
    series_select = $('#series_select');
    series_header = $('#series_header');
    timestamp_header = $('#timestamp_header');
    series_detail = $('#series_detail');
    timestamp_detail = $('#timestamp_detail');
    model_link = $('#download_model');
    var model_url = DATA_ROOT + "model.tar.gz";
    model_link.attr("href", model_url);
    ts_sequence_div(series_select);
    ts_sequence_div(series_detail);
    //add_ts_summary(series_select);
    var series_order = json_data.series_order;
    for (var i=0; i<series_order.length; i++) {
        var series_name = series_order[i];
        var series_display = $("<div/>").appendTo(series_select);
        series_display.css({"display": "flex", "flex-flow": "column"});
        var series_button = $(`<button>${series_name}</button>`).appendTo(series_display);
        series_button.click(series_callback(series_detail, series_name));
        add_ts_summary(series_display, series_name);
    }
    show_series_detail(series_detail);
};

var ts_sequence_div = function(div) {
    div.empty();
    div.css({"display": "flex", "flex-flow": "row wrap", "margin": "5px"});
};

var show_series_detail = function (div, series_name) {
    // SOMEDAY GET PATHS FROM MANIFEST WHEN MANIFEST IS FIXED...
    focus_timestamp = null;
    if (!series_name) {
        series_name = json_data.series_order[0];
    }
    series_header.html("Series: " + series_name);
    var series = json_data.series[series_name];
    var timestamp_order = series.timestamp_order;
    div.empty();
    for (var i=0; i<timestamp_order.length; i++) {
        var ts_num = timestamp_order[i];
        if (!focus_timestamp) {
            focus_timestamp = ts_num;
        }
        //var ts = series.timestamps[ts_num];
        //var ts_root = DATA_WEB + series_name + "/" + ts_num + "/";
        // xxxx fix the name to identify the series and ts
        //var data_path = ts_root + `${series_name}_${ts_num}.npz`;
        var ts_div = $("<div/>").appendTo(div);
        ts_div.css({"display": "flex", "flex-flow": "column"});
        //$(`<a href="${data_path}" style="color:blue">\u21d3 ${series_name}/${ts_num} </a>`).appendTo(ts_div);
        var ts_button = $(`<button> ${series_name}/${ts_num} </button>`).appendTo(ts_div);
        ts_button.click(ts_callback(series_name, ts_num));
        add_ts_summary(ts_div, series_name, ts_num);
    }
    focus_on_timestamp(series_name, focus_timestamp);
};

var series_callback = function(div, series_name) {
    return function () {
        info.html("Selected series " + series_name);
        show_series_detail(div, series_name);
        div[0].scrollIntoView();
    }
};

var ts_callback = function(series_name, ts_num) {
    return function () {
        info.html("Selected timestamp " + series_name + "/" + ts_num);
        focus_on_timestamp(series_name, ts_num);
        timestamp_detail[0].scrollIntoView();
    }
};

var focus_on_timestamp = function(series_name, ts_num, target_div, series_json) {
    target_div = target_div || timestamp_detail;
    series_json = series_json || json_data;
    if (timestamp_header) {
        timestamp_header.html(`Timestamp ${ts_num} in series ${series_name}`);
    }
    var series = series_json.series[series_name];
    var ts = series.timestamps[ts_num];
    var shape = ts.shape;
    var depth = shape[0];
    var ts_root = DATA_WEB + series_name + "/" + ts_num + "/";
    var ts_source = DATA_SOURCE + series_name + "/";
    var efn = ts_root + "extruded_volume.bin";
    var mfn = ts_root + "max_intensity_volume.bin";
    target_div.empty();
    var data_path = ts_source + `${series_name}_${ts_num}.npz`;
    $(`<a href="${data_path}" style="color:blue">Download \u21d3 ${series_name}/${ts_num} </a>`).
        appendTo(target_div);
    var ts_row = $("<div/>").appendTo(target_div);
    ts_row.css({"display": "flex", "flex-flow": "row", "margin": "5px"});
    var slider_wrap = $("<div/>").appendTo(ts_row);
    var slider = $("<div/>").appendTo(slider_wrap);
    slider.height(300);
    var slide_callback = function () {
        //debugger;
        var layer = slider.slider("option", "value");
        img.set_layer(layer);
        labels.set_layer(layer);
    };
    slider.slider({
        max: depth-1,
        min: 0,
        step: 1,
        value: depth-1,
        orientation: "vertical",
        slide: slide_callback,
    });
    var img = $("<div>img</div>").appendTo(ts_row);
    var labels = $("<div>layers</div>").appendTo(ts_row);
    slider_wrap.css({padding: "10px"});
    img.css({padding: "10px"});
    labels.css({padding: "10px"});
    var load_layers = function(to_div, from_url) {
        to_div.html("loading" + from_url);
        var request = new XMLHttpRequest();
        request.open('GET', from_url, true);
        request.responseType = 'blob';
        request.onload = function() {
            to_div.html("Binary loaded");
            var reader = new FileReader();
            reader.readAsArrayBuffer(request.response);
            //reader.readAsDataURL(request.response);
            reader.onload =  function() {
                to_div.empty();
                to_div.layers3d({
                    volume: reader.result,
                    shape: ts.shape,
                    layer: depth - 1,
                });
            };
        };
        request.onerror = on_binary_load_failure;
        request.send();
    };
    load_layers(img, mfn);
    load_layers(labels, efn);
}

var add_ts_summary = function(div, series_name, ts_num) {
    // SOMEDAY GET PATHS FROM MANIFEST WHEN MANIFEST IS FIXED...
    if (!series_name) {
        series_name = json_data.series_order[0];
    }
    if (!ts_num) {
        ts_num = json_data.series[series_name].timestamp_order[0];
    }
    var ts_root = DATA_WEB + series_name + "/" + ts_num + "/";
    var labels_image = ts_root + "extruded_colorized_labels.png";
    var intensity_image = ts_root + "max_intensity_image.png";
    var summary = $("<div/>").appendTo(div);
    summary.css({"display": "flex", "flex-flow": "column"});
    $(`<img src="${intensity_image}" width="100" style="margin:10px"/>`).appendTo(summary);
    $(`<img src="${labels_image}" width="100" style="margin:10px"/>`).appendTo(summary);
};

var on_binary_load_failure = function() {
    alert("Could not load local binary data.\n" + 
            "\n You may need to run a web server to avoid cross origin restrictions.")
};
